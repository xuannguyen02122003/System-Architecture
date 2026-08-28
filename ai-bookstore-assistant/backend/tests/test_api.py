"""
Tests for the FastAPI SSE endpoint.

We disable the presentation delay so the test runs fast, then parse the raw SSE
stream and assert that it contains trace events followed by the final answer.
"""
import json
import os

# Disable the artificial per-step delay for tests (read dynamically per request).
os.environ["SSE_STEP_DELAY_MS"] = "0"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    """Turn a raw SSE response body into a list of (event_type, data) pairs."""
    events = []
    for block in text.strip().split("\n\n"):
        etype, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                etype = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
        if etype:
            events.append((etype, json.loads(data) if data else {}))
    return events


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ask_streams_trace_then_answer():
    resp = client.post("/api/ask",
                       json={"question": "What books did Nguyen Van A buy in July?"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    types = [t for t, _ in events]

    # The stream must contain trace events, then exactly one answer, then done.
    assert "trace" in types
    assert types[-1] == "done"

    trace_events = [d for t, d in events if t == "trace"]
    assert trace_events[0]["phase"] == "REQUEST_RECEIVED"
    assert any(e["phase"] == "DATA_RETRIEVAL" for e in trace_events)

    answers = [d for t, d in events if t == "answer"]
    assert len(answers) == 1
    assert "Nguyen Van A" in answers[0]["answer"]


def test_ask_unknown_customer_streams_not_found():
    resp = client.post("/api/ask", json={"question": "What did Taylor Swift order?"})
    events = _parse_sse(resp.text)
    phases = [d["phase"] for t, d in events if t == "trace"]
    assert "NOT_FOUND" in phases
    answers = [d for t, d in events if t == "answer"]
    assert "couldn't find" in answers[0]["answer"].lower()
