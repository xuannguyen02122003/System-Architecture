"""
Tests for the LLM layer's stub and the auto-selection factory.

We don't test the real OpenAI call here (it needs a key and a network); we verify
the deterministic pieces: intent classification, entity/period parsing, and that
`get_llm()` falls back to the stub when no key is configured.
"""
from app.llm import StubLLM, get_llm, parse_period, extract_person_name


def test_stub_classifies_intents():
    stub = StubLLM()
    assert stub.analyze("What did Nguyen Van A buy in July?").intent == "order_history"
    assert stub.analyze("How many orders were placed in Q2 2026?").intent == "order_count"
    assert stub.analyze("What is the return policy?").intent == "policy_lookup"
    assert stub.analyze("Show me science books").intent == "book_search"
    assert stub.analyze("Tell me a joke").intent == "unknown"


def test_parse_period():
    assert parse_period("in July 2026") == ("2026-07-01", "2026-07-31", "July 2026")
    start, end, label = parse_period("Q2 2026")
    assert (start, end, label) == ("2026-04-01", "2026-06-30", "Q2 2026")
    assert parse_period("no date here") == (None, None, None)


def test_extract_person_name():
    assert extract_person_name("What did Nguyen Van A buy?") == "Nguyen Van A"
    assert extract_person_name("What did Taylor Swift order?") == "Taylor Swift"
    assert extract_person_name("How many orders in Q2 2026?") is None


def test_get_llm_falls_back_to_stub_without_key(monkeypatch):
    monkeypatch.setattr("app.config.LLM_API_KEY", "", raising=False)
    assert isinstance(get_llm(), StubLLM)
