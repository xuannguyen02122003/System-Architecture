"""
Ask the assistant a question from the terminal and watch the execution trace
print live — a preview of what the visual trace panel will show later.

Usage (from the backend/ folder, with the venv active):
    python -m scripts.ask "What books did Nguyen Van A buy in July?"

If you don't pass a question, a default demo question is used.
"""
import sys

from app.events import TraceEvent, Status
from app.orchestrator import run_query


# ASCII markers so it renders cleanly on any terminal (including Windows).
_MARK = {
    Status.RUNNING: "  ..",
    Status.COMPLETED: "  ok",
    Status.FAILED: "  XX",
    Status.INFO: "*",
}


def print_event(ev: TraceEvent) -> None:
    """Called live as each event is emitted by the pipeline."""
    mark = _MARK.get(ev.status, "  ?")
    line = f"{mark} [{ev.seq:>2}] {ev.phase:<17} {ev.label}"

    # For completed steps, append the interesting metadata.
    extras = []
    if ev.source:
        extras.append(f"source={ev.source}")
    if ev.query:
        extras.append(f"query=({ev.query})")
    if ev.records_found is not None:
        extras.append(f"records={ev.records_found}")
    if ev.duration_ms is not None:
        extras.append(f"{ev.duration_ms}ms")
    if extras and ev.status != Status.RUNNING:
        line += "  ->  " + " | ".join(extras)
    print(line)


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "What books did Nguyen Van A buy in July?"

    print("\nQUESTION:", question)
    print("-" * 78)
    result = run_query(question, on_event=print_event)   # live-print each event
    print("-" * 78)
    print("ANSWER:  ", result["answer"], "\n")


if __name__ == "__main__":
    main()
