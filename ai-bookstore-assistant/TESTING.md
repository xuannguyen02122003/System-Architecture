# Testing

This project is tested at two levels: automated tests for the backend logic and
API, and a manual checklist for the UI and real-time behaviour.

## Run the automated tests

From the `backend/` folder (with the virtual environment active):

```bash
python -m pytest -v
```

All tests should pass (currently **22**). The frontend is type-checked and
compiled by its build:

```bash
cd frontend
npm run build      # runs `tsc` then `vite build`; fails on any type error
```

## Test matrix

Every scenario the brief asks for maps to a concrete automated test.

| # | Scenario | What it proves | Test |
| - | -------- | -------------- | ---- |
| 1 | Successful retrieval | A normal question returns the right records | `test_retrieval.py::test_find_customer_resolves_name` |
| 2 | Multiple data sources | One question spans customers → orders → order_items | `test_orchestrator.py::test_order_history_multi_source` |
| 3 | Aggregation | Counting/summing over structured data | `test_orchestrator.py::test_order_count_aggregation` |
| 4 | Unstructured documents | Policy questions hit the document search | `test_orchestrator.py::test_policy_lookup` |
| 5 | Missing information (no such entity) | Unknown customer → NOT_FOUND, not a made-up answer | `test_orchestrator.py::test_unknown_customer_is_not_hallucinated` |
| 6 | Valid entity, empty result | Real customer, no orders in the period → honest "none" | `test_orchestrator.py::test_known_customer_but_no_orders_in_period` |
| 7 | Invalid / out-of-scope question | Gibberish → a helpful "please rephrase" | `test_orchestrator.py::test_unknown_intent_asks_to_rephrase` |
| 8 | Hallucination resistance (documents) | No relevant document → empty, not invented | `test_retrieval.py::test_search_documents_no_match` |
| 9 | Real-time streaming | The API streams trace events then an answer | `test_api.py::test_ask_streams_trace_then_answer` |
| 10 | Empty question | Blank input → a clean error, no crash | `test_api.py::test_ask_empty_question_streams_error` |
| 11 | Backend / retrieval error | A data-layer failure becomes a visible ERROR event, no 500/hang | `test_api.py::test_retrieval_error_is_surfaced_not_crashed` |
| 12 | LLM fallback | With no API key, the app uses the deterministic stub | `test_llm.py::test_get_llm_falls_back_to_stub_without_key` |

## Manual UI checklist

Start both servers (see the README quickstart), then verify:

- [ ] Clicking each example question streams the trace **step by step** (nodes
      appear one at a time, spinner → green check).
- [ ] The answer appears on the left with the correct intent badge and the
      "Data sources used" chips.
- [ ] "What did Taylor Swift order?" shows a **Not found** node (amber) and an
      honest answer — no invented orders.
- [ ] "What is the return policy?" cites `return-policy.txt` with a clean,
      whole-word snippet.
- [ ] The **Raw events** toggle reveals the underlying JSON events.
- [ ] Stop the backend and ask a question → the UI shows a friendly
      "Could not reach the server" message instead of failing silently.
