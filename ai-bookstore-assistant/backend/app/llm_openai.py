"""
The real LLM implementation (OpenAI-compatible).

This is the drop-in replacement for StubLLM. It implements the SAME two methods
(analyze, synthesize), so nothing else in the codebase changes when we switch to
it. The switch is automatic: see `get_llm()` in llm.py — if an API key is
configured, this class is used; otherwise the deterministic stub is.

The hybrid design is preserved:
  - analyze()   : the model classifies intent and extracts entity *strings*
                  (customer name, time phrase, genre). We then reuse the
                  deterministic `parse_period()` to turn "July" into a real date
                  range — dates are too important to leave to free-text.
  - synthesize(): the model writes the final answer, but is given ONLY the
                  retrieved records and is instructed to never invent anything.
                  (The orchestrator still short-circuits "not found" cases before
                  they ever reach the model, so it cannot hallucinate an entity
                  that doesn't exist.)
"""
from __future__ import annotations

import json

from . import config
from .llm import BaseLLM, QueryPlan, GENRES, parse_period


_ANALYZE_SYSTEM = f"""You analyze questions for an online bookstore assistant.
Classify the question and extract entities. Respond with a JSON object ONLY:

{{
  "intent": one of ["order_history","order_count","policy_lookup","book_search","unknown"],
  "customer_name": string or null,   // a person's name, if the question is about one
  "period_text": string or null,     // the time phrase exactly as written, e.g. "July", "Q2 2026"
  "genre": one of {GENRES} or null,
  "author": string or null,
  "keyword": string or null
}}

Definitions:
- order_history: what a specific customer bought/ordered.
- order_count: how many orders were placed (a count), possibly over a period.
- policy_lookup: returns, refunds, shipping, payment, membership, FAQ, store info.
- book_search: browsing the catalogue by genre/author/title.
- unknown: anything else.
Return valid JSON with no commentary."""


_SYNTHESIZE_SYSTEM = (
    "You are the assistant for the online bookstore 'Kamiya Bookstore'. "
    "Answer the user's question using ONLY the data provided in CONTEXT. "
    "If CONTEXT is empty or does not contain the answer, clearly say you could "
    "not find the information — do NOT guess or invent titles, names, numbers, "
    "or policies. Be concise and friendly. When relevant, cite order IDs like "
    "#5007 or the document name you used."
)


class OpenAILLM(BaseLLM):
    def __init__(self) -> None:
        # Imported lazily so the package is only required when a key is set.
        from openai import OpenAI
        self.client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
        self.model = config.LLM_MODEL

    def analyze(self, question: str) -> QueryPlan:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _ANALYZE_SYSTEM},
                {"role": "user", "content": question},
            ],
        )
        data = json.loads(resp.choices[0].message.content or "{}")

        intent = data.get("intent") or "unknown"
        # Deterministic date handling — reuse the same parser the stub uses.
        date_from, date_to, period_label = parse_period(
            data.get("period_text") or question
        )
        entities = {
            "customer_name": data.get("customer_name"),
            "date_from": date_from,
            "date_to": date_to,
            "period_label": period_label,
            "genre": data.get("genre"),
            "author": data.get("author"),
            "keyword": data.get("keyword"),
        }
        return QueryPlan(intent=intent, entities=entities,
                         rationale="Analyzed by LLM (intent + entity extraction).")

    def synthesize(self, question: str, plan: QueryPlan, context: dict) -> str:
        user = (f"QUESTION: {question}\n\n"
                f"CONTEXT (the only data you may use):\n"
                f"{json.dumps(context, ensure_ascii=False, default=str, indent=2)}")
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": _SYNTHESIZE_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
