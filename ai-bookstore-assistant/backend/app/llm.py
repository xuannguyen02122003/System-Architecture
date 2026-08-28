"""
The LLM layer — the two "fuzzy" jobs in the pipeline:

  1. analyze()   : natural-language question  ->  structured QueryPlan
  2. synthesize(): retrieved records          ->  grounded natural-language answer

We define a small interface (BaseLLM) and a deterministic StubLLM that needs no
API key. This lets the whole system run and be demoed offline. In Stage 6 we add
a real OpenAI-compatible implementation with the SAME two methods, so nothing
else in the codebase has to change.

Why a stub that uses rules? Two reasons:
  - It keeps the demo 100% reproducible while we build the rest of the system.
  - It makes the boundary explicit: analysis and synthesis are the ONLY places
    the model is used. Everything in between (the actual data access) is exact,
    deterministic Python — which is what keeps answers grounded and traceable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import calendar
import re


GENRES = ["Non-Fiction", "Fiction", "Science", "History", "Children", "Technology"]

# Capitalized words that are NOT names — so we don't mistake "What" or "July"
# for a customer. (The real LLM in Stage 6 handles this far more robustly; this
# is a pragmatic stub.)
_NON_NAME_WORDS = {
    "What", "Which", "Who", "When", "Where", "Why", "How", "Is", "Are", "Do",
    "Does", "Did", "Can", "Could", "Would", "Show", "List", "Give", "Tell",
    "In", "On", "At", "The", "I", "My", "Our", "Your", "Please",
    "Q1", "Q2", "Q3", "Q4",
}
# Note: single letters like "A" are intentionally NOT excluded, because
# Vietnamese names can end in one (e.g. "Nguyen Van A").
_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}


@dataclass
class QueryPlan:
    """The structured understanding of a question that drives retrieval."""
    intent: str                              # order_history | order_count | policy_lookup | book_search | unknown
    entities: dict = field(default_factory=dict)
    rationale: str = ""


# --------------------------------------------------------------------------- #
# Small deterministic parsers (shared helpers)
# --------------------------------------------------------------------------- #
def _extract_year(text: str) -> int:
    match = re.search(r"\b(20\d{2})\b", text)
    return int(match.group(1)) if match else 2026   # our dataset lives in 2026


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    last = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last:02d}"


def parse_period(text: str) -> tuple[str | None, str | None, str | None]:
    """Turn phrases like 'in July', 'Q2 2026', or '2026' into a date range.

    Returns (date_from, date_to, human_label). Any of them may be None, meaning
    'no date filter'.
    """
    low = text.lower()
    year = _extract_year(text)

    # Quarters: Q1..Q4 or "first/second/third/fourth quarter"
    quarters = {
        1: (["q1", "first quarter"], (1, 3)),
        2: (["q2", "second quarter"], (4, 6)),
        3: (["q3", "third quarter"], (7, 9)),
        4: (["q4", "fourth quarter"], (10, 12)),
    }
    for q, (keys, (m1, m2)) in quarters.items():
        if any(k in low for k in keys):
            start = f"{year}-{m1:02d}-01"
            end = f"{year}-{m2:02d}-{calendar.monthrange(year, m2)[1]:02d}"
            return start, end, f"Q{q} {year}"

    # Named months: "in July", "July 2026"
    for name, month in _MONTHS.items():
        if re.search(rf"\b{name}\b", low):
            start, end = _month_bounds(year, month)
            return start, end, f"{name.capitalize()} {year}"

    # A bare year: "in 2026"
    if re.search(r"\b20\d{2}\b", text):
        return f"{year}-01-01", f"{year}-12-31", str(year)

    return None, None, None


def extract_person_name(text: str) -> str | None:
    """Grab the most likely person name: the longest run of capitalized words
    that aren't question words or month names. Deterministic and DB-free — if
    the guessed name isn't a real customer, retrieval simply finds nothing."""
    tokens = re.findall(r"[A-Za-z]+", text)
    runs: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        is_name_like = (
            tok[:1].isupper()
            and tok not in _NON_NAME_WORDS
            and tok.lower() not in _MONTHS
        )
        if is_name_like:
            current.append(tok)
        else:
            if current:
                runs.append(current)
                current = []
    if current:
        runs.append(current)
    names = [" ".join(r) for r in runs]
    return max(names, key=len) if names else None


def _detect_genre(text: str) -> str | None:
    low = text.lower()
    for genre in GENRES:
        if genre.lower() in low:
            return genre
    return None


# --------------------------------------------------------------------------- #
# The interface + the stub implementation
# --------------------------------------------------------------------------- #
class BaseLLM:
    """The contract both the stub and the real model implement."""
    def analyze(self, question: str) -> QueryPlan:
        raise NotImplementedError

    def synthesize(self, question: str, plan: QueryPlan, context: dict) -> str:
        raise NotImplementedError


class StubLLM(BaseLLM):
    """A rule-based stand-in for a real LLM. No network, fully deterministic."""

    # -- 1) Understand the question ---------------------------------------- #
    def analyze(self, question: str) -> QueryPlan:
        low = question.lower()
        date_from, date_to, period_label = parse_period(question)

        policy_words = ("return", "refund", "shipping", "ship ", "policy",
                        "payment", " pay", "membership", "loyalty", "faq",
                        "hours", "contact", "warranty", "cancel")
        order_words = ("buy", "bought", "purchase", "order", "ordered", "spend", "spent")
        book_words = ("book", "title", "author", "genre", "recommend", "novel")

        if any(w in low for w in policy_words):
            intent = "policy_lookup"
            entities = {}
            rationale = "Question mentions a store policy / support topic."
        elif "how many" in low and "order" in low:
            intent = "order_count"
            entities = {"date_from": date_from, "date_to": date_to,
                        "period_label": period_label}
            rationale = "Counting question about orders over a period."
        elif any(w in low for w in order_words):
            intent = "order_history"
            entities = {"customer_name": extract_person_name(question),
                        "date_from": date_from, "date_to": date_to,
                        "period_label": period_label}
            rationale = "Asks what a customer bought / ordered."
        elif any(w in low for w in book_words):
            intent = "book_search"
            entities = {"genre": _detect_genre(question),
                        "author": None, "keyword": None}
            rationale = "Asks about the book catalogue."
        else:
            intent = "unknown"
            entities = {}
            rationale = "No known intent matched."

        return QueryPlan(intent=intent, entities=entities, rationale=rationale)

    # -- 2) Write the answer from retrieved data --------------------------- #
    def synthesize(self, question: str, plan: QueryPlan, context: dict) -> str:
        intent = plan.intent
        if intent == "order_history":
            return self._answer_order_history(plan, context)
        if intent == "order_count":
            return self._answer_order_count(plan, context)
        if intent == "policy_lookup":
            return self._answer_policy(context)
        if intent == "book_search":
            return self._answer_books(context)
        return ("I can answer questions about customers, their orders, our book "
                "catalogue, and store policies. Could you rephrase your question?")

    # -- templated, grounded answers --------------------------------------- #
    @staticmethod
    def _answer_order_history(plan: QueryPlan, context: dict) -> str:
        customer = context["customer"]["name"]
        period = plan.entities.get("period_label") or "the available records"
        orders = context.get("orders", [])
        items = context.get("items", [])
        if not orders:
            return f"I couldn't find any orders for {customer} in {period}."

        # Aggregate quantities per title (grounded strictly in retrieved rows).
        by_title: dict[str, int] = {}
        for row in items:
            by_title[row["title"]] = by_title.get(row["title"], 0) + row["quantity"]
        parts = [t + (f" (x{q})" if q > 1 else "") for t, q in by_title.items()]
        order_ids = ", ".join(f"#{o['order_id']}" for o in orders)
        return (f"In {period}, {customer} purchased: {', '.join(parts)}. "
                f"(Orders {order_ids}.)")

    @staticmethod
    def _answer_order_count(plan: QueryPlan, context: dict) -> str:
        rec = context["count"]
        period = plan.entities.get("period_label") or "all time"
        return (f"There were {rec['order_count']} orders in {period}, "
                f"totaling ${rec['total_revenue']:.2f}.")

    @staticmethod
    def _answer_policy(context: dict) -> str:
        docs = context.get("documents", [])
        if not docs:
            return "I couldn't find that information in our store documents."
        top = docs[0]
        return f"According to {top['document']}: {top['snippet']}"

    @staticmethod
    def _answer_books(context: dict) -> str:
        books = context.get("books", [])
        if not books:
            return "I couldn't find any books matching that description."
        listed = "; ".join(f"{b['title']} by {b['author']} (${b['price']:.2f})"
                           for b in books[:10])
        return f"We have {len(books)} matching title(s): {listed}."
