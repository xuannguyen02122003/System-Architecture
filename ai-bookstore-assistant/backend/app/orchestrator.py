"""
The orchestrator — the brain that runs one question through the pipeline:

    analyze  ->  select sources  ->  retrieve  ->  synthesize

It is the ONLY place that emits trace events, so the trace can never drift out of
sync with what actually ran: emitting an event *is* how each step is performed.

The retrieval layer stays deterministic; the LLM (real or stub) is used only to
understand the question and to phrase the final answer from retrieved records.
If a required entity isn't found (unknown customer, no matching document), the
pipeline says so via a NOT_FOUND event and a plain "not found" answer — it never
invents data.
"""
from __future__ import annotations

from typing import Callable, Optional

from . import retrieval
from .events import Tracer, TraceEvent, Phase
from .llm import BaseLLM, get_llm, QueryPlan


def _select_sources(intent: str) -> list[str]:
    """Rule-based mapping from intent to the data sources it needs."""
    return {
        "order_history": ["customers", "orders", "order_items"],
        "order_count": ["orders"],
        "policy_lookup": ["documents"],
        "book_search": ["books"],
        "unknown": [],
    }.get(intent, [])


def run_query(question: str,
              llm: Optional[BaseLLM] = None,
              on_event: Optional[Callable[[TraceEvent], None]] = None) -> dict:
    """Run one question end-to-end. Returns the answer plus the full event trace.

    `on_event` is called live as each event is emitted (used by the SSE stage);
    if omitted, events are simply collected and returned.
    """
    llm = llm or get_llm()
    tracer = Tracer(on_event=on_event)

    tracer.mark(Phase.REQUEST_RECEIVED, "User question received", question=question)

    # 1) Analyze the question -> structured plan
    with tracer.step(Phase.QUERY_ANALYSIS, "Analyze the question") as s:
        plan = llm.analyze(question)
        s.query = f"intent = {plan.intent}"
        s.detail = {"intent": plan.intent, "entities": plan.entities,
                    "rationale": plan.rationale}

    # 2) Decide which data sources are needed
    with tracer.step(Phase.SOURCE_SELECTION, "Select data sources") as s:
        sources = _select_sources(plan.intent)
        s.query = ", ".join(sources) if sources else "none"
        s.detail = {"sources": sources}

    # 3) Retrieve (branch by intent). A branch may return a terminal answer
    #    directly (e.g. customer not found) to short-circuit synthesis.
    answer: Optional[str] = None
    context: dict = {}

    if plan.intent == "order_history":
        answer, context = _retrieve_order_history(tracer, plan)
    elif plan.intent == "order_count":
        context = _retrieve_order_count(tracer, plan)
    elif plan.intent == "policy_lookup":
        context = _retrieve_policy(tracer, question)
    elif plan.intent == "book_search":
        context = _retrieve_books(tracer, plan)
    # 'unknown' intent: no retrieval; synthesize() returns a helpful fallback.

    # 4) Generate the answer (unless a branch already produced a terminal one)
    if answer is None:
        with tracer.step(Phase.ANSWER_GENERATION, "Generate grounded answer") as s:
            answer = llm.synthesize(question, plan, context)
            s.detail = {"answer_preview": answer[:160]}

    tracer.mark(Phase.COMPLETED, "Response ready", answer=answer)

    return {
        "question": question,
        "intent": plan.intent,
        "answer": answer,
        "events": tracer.as_dicts(),
    }


# --------------------------------------------------------------------------- #
# Retrieval branches — each emits DATA_RETRIEVAL events as it works.
# --------------------------------------------------------------------------- #
def _retrieve_order_history(tracer: Tracer, plan: QueryPlan):
    """customer name -> customer_id -> orders -> line items (books)."""
    context: dict = {}
    name = plan.entities.get("customer_name")

    if not name:
        tracer.mark(Phase.NOT_FOUND, "No customer name found in the question")
        return ("I couldn't tell which customer you're asking about — "
                "please include the customer's name."), context

    with tracer.step(Phase.DATA_RETRIEVAL, f"Look up customer '{name}'",
                     source="customers") as s:
        res = retrieval.find_customer(name)
        s.query, s.records_found = res.query, res.records_found

    if res.records_found == 0:
        tracer.mark(Phase.NOT_FOUND, f"No customer matching '{name}'", searched=name)
        return f"I couldn't find any customer named '{name}' in our records.", context

    customer = res.records[0]
    context["customer"] = customer

    with tracer.step(Phase.DATA_RETRIEVAL, "Search this customer's orders",
                     source="orders") as s:
        res_orders = retrieval.search_orders(
            customer_id=customer["customer_id"],
            date_from=plan.entities.get("date_from"),
            date_to=plan.entities.get("date_to"),
        )
        s.query, s.records_found = res_orders.query, res_orders.records_found
    context["orders"] = res_orders.records

    if res_orders.records:
        order_ids = [o["order_id"] for o in res_orders.records]
        with tracer.step(Phase.DATA_RETRIEVAL, "Fetch the books in those orders",
                         source="order_items") as s:
            res_items = retrieval.get_order_items(order_ids)
            s.query, s.records_found = res_items.query, res_items.records_found
        context["items"] = res_items.records
    else:
        context["items"] = []

    return None, context   # let synthesis phrase the final answer


def _retrieve_order_count(tracer: Tracer, plan: QueryPlan) -> dict:
    with tracer.step(Phase.DATA_RETRIEVAL, "Count matching orders",
                     source="orders") as s:
        res = retrieval.count_orders(
            date_from=plan.entities.get("date_from"),
            date_to=plan.entities.get("date_to"),
        )
        s.query, s.records_found = res.query, res.records_found
        s.detail = {"result": res.records[0]}
    return {"count": res.records[0]}


def _retrieve_policy(tracer: Tracer, question: str) -> dict:
    with tracer.step(Phase.DATA_RETRIEVAL, "Search store documents",
                     source="documents") as s:
        res = retrieval.search_documents(question)
        s.query, s.records_found = res.query, res.records_found
        s.detail = {"documents": [r["document"] for r in res.records]}
    if res.records_found == 0:
        tracer.mark(Phase.NOT_FOUND, "No matching store document")
    return {"documents": res.records}


def _retrieve_books(tracer: Tracer, plan: QueryPlan) -> dict:
    with tracer.step(Phase.DATA_RETRIEVAL, "Search the book catalogue",
                     source="books") as s:
        res = retrieval.search_books(
            keyword=plan.entities.get("keyword"),
            genre=plan.entities.get("genre"),
            author=plan.entities.get("author"),
        )
        s.query, s.records_found = res.query, res.records_found
    return {"books": res.records}
