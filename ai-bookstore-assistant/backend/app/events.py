"""
The execution-trace event model.

This is the observability layer — the thing that makes the app more than a
black-box chatbot. As the pipeline runs, it emits small, structured events that
describe *observable system actions* (which source was searched, what filter was
used, how many records came back, how long it took). It deliberately does NOT
expose any LLM private reasoning — only what the system actually did.

Key design idea: each step emits TWO events — a "running" event when it starts
and a "completed" (or "failed") event when it ends. That pair is what lets the
frontend animate a node from spinner -> green check, and it means the trace is a
faithful record of execution, not a script written after the fact.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import time
from typing import Callable, Iterator, Optional


# The phases of the pipeline. Using an enum-like set of constants keeps the
# event "type" consistent everywhere (no typos like "RETRIEVAL" vs "RETRIEVE").
class Phase:
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    QUERY_ANALYSIS = "QUERY_ANALYSIS"
    SOURCE_SELECTION = "SOURCE_SELECTION"
    DATA_RETRIEVAL = "DATA_RETRIEVAL"
    ANSWER_GENERATION = "ANSWER_GENERATION"
    COMPLETED = "COMPLETED"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


class Status:
    RUNNING = "running"      # step has started
    COMPLETED = "completed"  # step finished successfully
    FAILED = "failed"        # step raised an error
    INFO = "info"            # a one-shot marker (no start/end pair)


def _now_iso() -> str:
    """Current UTC time as an ISO-8601 string (for timestamps in the trace)."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class TraceEvent:
    """One observable step in the pipeline. This is the contract the frontend
    consumes; every field here can be shown in the trace panel."""
    seq: int                                    # order of the event (1, 2, 3...)
    phase: str                                  # one of Phase.*
    label: str                                  # human-readable description
    status: str                                 # one of Status.*
    started_at: str                             # ISO timestamp
    source: Optional[str] = None                # which data source (e.g. "orders")
    query: Optional[str] = None                 # the filter/query that ran
    records_found: Optional[int] = None         # how many records came back
    duration_ms: Optional[float] = None         # how long the step took
    detail: dict = field(default_factory=dict)  # any extra structured info

    def to_dict(self) -> dict:
        return asdict(self)


class StepHandle:
    """A tiny mutable object handed to the body of a `with tracer.step(...)`
    block, so the code inside can report what it found. Whatever it sets here is
    copied onto the "completed" event when the step ends."""
    def __init__(self) -> None:
        self.source: Optional[str] = None
        self.query: Optional[str] = None
        self.records_found: Optional[int] = None
        self.detail: dict = {}


class Tracer:
    """Collects trace events for a single question run.

    - Assigns each event an increasing sequence number.
    - Optionally calls `on_event` the moment an event is emitted. Right now the
      scripts just collect events; in the SSE stage, `on_event` is how each event
      is pushed live to the browser. Designing that hook in now means the
      streaming stage needs no changes here.
    """
    def __init__(self, on_event: Optional[Callable[[TraceEvent], None]] = None) -> None:
        self._seq = 0
        self.events: list[TraceEvent] = []
        self._on_event = on_event

    def _emit(self, phase: str, label: str, status: str, **kwargs) -> TraceEvent:
        self._seq += 1
        event = TraceEvent(seq=self._seq, phase=phase, label=label,
                           status=status, started_at=_now_iso(), **kwargs)
        self.events.append(event)
        if self._on_event:
            self._on_event(event)
        return event

    def mark(self, phase: str, label: str, **detail) -> TraceEvent:
        """Emit a single one-shot event (no start/end pair). Used for markers
        like REQUEST_RECEIVED, NOT_FOUND, and COMPLETED."""
        return self._emit(phase, label, Status.INFO, detail=detail)

    @contextmanager
    def step(self, phase: str, label: str, source: Optional[str] = None) -> Iterator[StepHandle]:
        """Wrap a unit of work. Emits a 'running' event, runs the body, then a
        'completed' event with the measured duration — or a 'failed' event if
        the body raises. Timing and error handling live here, once, so every
        step is instrumented identically."""
        handle = StepHandle()
        handle.source = source
        start = time.perf_counter()
        self._emit(phase, label, Status.RUNNING, source=source)
        try:
            yield handle
        except Exception as exc:  # any failure becomes a visible ERROR event
            duration = (time.perf_counter() - start) * 1000
            self._emit(Phase.ERROR, f"{label} — failed", Status.FAILED,
                       source=handle.source, duration_ms=round(duration, 1),
                       detail={"error": str(exc)})
            raise
        else:
            duration = (time.perf_counter() - start) * 1000
            self._emit(phase, label, Status.COMPLETED,
                       source=handle.source, query=handle.query,
                       records_found=handle.records_found,
                       duration_ms=round(duration, 1), detail=handle.detail)

    def as_dicts(self) -> list[dict]:
        return [e.to_dict() for e in self.events]
