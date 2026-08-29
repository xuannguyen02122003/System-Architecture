"""
The FastAPI web server.

It exposes two endpoints:
  GET  /api/health  -> a simple liveness check
  POST /api/ask     -> runs a question and STREAMS the execution trace back to
                       the browser as Server-Sent Events (SSE), finishing with
                       the answer.

Why SSE (and not WebSockets)? The trace only ever flows one way — server to
browser — so we don't need a bidirectional channel. SSE is just a long-lived
HTTP response with a special content type, which is far simpler to build and
debug, and it reconnects automatically.

Concurrency detail: the pipeline (`run_query`) is ordinary synchronous Python
that emits events through a callback. To stream those events live, we run the
pipeline in a background thread that pushes each event onto a thread-safe queue,
while the async endpoint drains that queue and yields one SSE message per event.
"""
from __future__ import annotations

import asyncio
import json
import os
import queue
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .orchestrator import run_query

app = FastAPI(title="Kamiya Bookstore — AI Data Assistant")

# Allow the React dev server (a different port) to call this API during
# development. For a local PoC, allowing all origins is fine and keeps setup easy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


def _sse(event_type: str, data: dict) -> str:
    """Format one Server-Sent Event. The wire format is literally:

        event: <type>
        data: <json>
        <blank line>
    """
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-data-assistant"}


@app.post("/api/ask")
async def ask(request: AskRequest) -> StreamingResponse:
    question = request.question.strip()

    # A small per-event delay makes the pipeline visibly step through the trace
    # in the UI (the pipeline itself runs in milliseconds). It only paces the
    # *presentation* — the core logic and tests stay fast. Set to 0 to disable.
    delay_ms = int(os.getenv("SSE_STEP_DELAY_MS", "250"))

    event_queue: "queue.Queue" = queue.Queue()
    DONE = object()   # sentinel marking the end of the stream

    def run_pipeline() -> None:
        """Runs in a background thread; pushes every trace event to the queue."""
        try:
            if not question:
                event_queue.put(("error", {"message": "Empty question."}))
            else:
                result = run_query(
                    question,
                    on_event=lambda ev: event_queue.put(("trace", ev.to_dict())),
                )
                event_queue.put(("answer", {
                    "question": result["question"],
                    "intent": result["intent"],
                    "answer": result["answer"],
                }))
        except Exception as exc:  # surface any failure as a stream event
            event_queue.put(("error", {"message": str(exc)}))
        finally:
            event_queue.put((DONE, None))

    async def event_stream():
        threading.Thread(target=run_pipeline, daemon=True).start()
        loop = asyncio.get_event_loop()
        while True:
            # queue.get() blocks, so run it in a threadpool to avoid blocking
            # the async event loop.
            kind, payload = await loop.run_in_executor(None, event_queue.get)
            if kind is DONE:
                break
            yield _sse(kind, payload)
            if kind == "trace" and delay_ms:
                await asyncio.sleep(delay_ms / 1000)
        yield _sse("done", {})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # disable proxy buffering so events flush live
        },
    )
