"""
End-to-end tests for the orchestrator pipeline (using the deterministic stub).

Each test is one of the demo questions, checking BOTH the final answer and that
the trace contains the right phases. This is what proves the "no hallucination"
behaviour: unknown people and missing documents produce NOT_FOUND, not fiction.
"""
from app.orchestrator import run_query
from app.events import Phase


def _phases(result) -> list[str]:
    return [e["phase"] for e in result["events"]]


def test_order_history_multi_source():
    result = run_query("What books did Nguyen Van A buy in July?")
    assert result["intent"] == "order_history"
    answer = result["answer"]
    for title in ["The Data-Driven Mind", "Python for Analysts",
                  "Deep Work Habits", "Mindful Money"]:
        assert title in answer
    assert "(x2)" in answer                       # Deep Work Habits bought twice
    # The trace must always open with a request and close with completion.
    assert _phases(result)[0] == Phase.REQUEST_RECEIVED
    assert _phases(result)[-1] == Phase.COMPLETED
    # It genuinely touched three sources.
    sources = {e["source"] for e in result["events"] if e["source"]}
    assert {"customers", "orders", "order_items"} <= sources


def test_order_count_aggregation():
    result = run_query("How many orders were placed in Q2 2026?")
    assert result["intent"] == "order_count"
    assert "8 orders" in result["answer"]
    assert "Q2 2026" in result["answer"]


def test_policy_lookup():
    result = run_query("What is the return policy?")
    assert result["intent"] == "policy_lookup"
    assert "return-policy.txt" in result["answer"]


def test_unknown_customer_is_not_hallucinated():
    result = run_query("What did Taylor Swift order?")
    assert result["intent"] == "order_history"
    assert "couldn't find" in result["answer"].lower()
    assert "Taylor Swift" in result["answer"]
    assert Phase.NOT_FOUND in _phases(result)     # honest "not found" in the trace


def test_unknown_intent_asks_to_rephrase():
    result = run_query("Tell me a joke about penguins")
    assert result["intent"] == "unknown"
    assert "rephrase" in result["answer"].lower()
