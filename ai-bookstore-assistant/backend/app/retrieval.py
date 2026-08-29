"""
The data retrieval layer.

This is the deterministic core of the system. Each function is a "tool" the
agent can call. Crucially, every tool returns not just the records it found, but
also a human-readable description of the *query it ran* — because the execution
trace needs to show "what filter was applied", not just "some rows came back".

Design rules kept deliberately simple:
  - Structured data (customers, books, orders) -> real SQL over SQLite.
  - Unstructured data (policy documents) -> keyword search (BM25). No vector DB;
    at this scale keyword search is exact, fast, and easy to explain.
  - No tool ever invents data. If nothing matches, it returns zero records and
    the caller decides how to respond.
"""
# Lets us write modern type hints like `int | None` even on Python 3.9, by
# treating all annotations as strings that are never evaluated at runtime.
from __future__ import annotations

from dataclasses import dataclass, field
import re

from .db import get_connection, rows_to_dicts
from .config import DOCS_DIR


@dataclass
class RetrievalResult:
    """The uniform shape every retrieval tool returns."""
    source: str                    # which data source was searched
    query: str                     # human-readable filter that was applied
    records: list[dict] = field(default_factory=list)

    @property
    def records_found(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "query": self.query,
            "records_found": self.records_found,
            "records": self.records,
        }


# --------------------------------------------------------------------------- #
# Structured-data tools (SQLite)
# --------------------------------------------------------------------------- #
def find_customer(name: str) -> RetrievalResult:
    """Resolve a (possibly partial) customer name to customer record(s)."""
    sql = "SELECT * FROM customers WHERE LOWER(name) LIKE '%' || LOWER(?) || '%'"
    conn = get_connection()
    try:
        rows = conn.execute(sql, (name,)).fetchall()
    finally:
        conn.close()
    return RetrievalResult(
        source="customers",
        query=f"name LIKE '%{name}%'",
        records=rows_to_dicts(rows),
    )


def search_orders(customer_id: int | None = None,
                  date_from: str | None = None,
                  date_to: str | None = None,
                  status: str | None = None) -> RetrievalResult:
    """Find orders, filtered by any combination of customer, date range, status.

    Dates are ISO strings (YYYY-MM-DD); because that format sorts
    lexicographically, plain string comparison works as a date comparison.
    """
    clauses, params, described = [], [], []
    if customer_id is not None:
        clauses.append("customer_id = ?"); params.append(customer_id)
        described.append(f"customer_id={customer_id}")
    if date_from:
        clauses.append("order_date >= ?"); params.append(date_from)
        described.append(f"date>={date_from}")
    if date_to:
        clauses.append("order_date <= ?"); params.append(date_to)
        described.append(f"date<={date_to}")
    if status:
        clauses.append("LOWER(status) = LOWER(?)"); params.append(status)
        described.append(f"status={status}")

    where = " AND ".join(clauses) if clauses else "1=1"
    sql = f"SELECT * FROM orders WHERE {where} ORDER BY order_date"
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return RetrievalResult(
        source="orders",
        query=" AND ".join(described) if described else "all orders",
        records=rows_to_dicts(rows),
    )


def get_order_items(order_ids: list[int]) -> RetrievalResult:
    """Given order ids, return the books in those orders (joined to titles)."""
    if not order_ids:
        return RetrievalResult(source="order_items", query="no order ids", records=[])

    placeholders = ", ".join("?" for _ in order_ids)
    sql = f"""
        SELECT oi.order_id, oi.book_id, b.title, b.author,
               oi.quantity, oi.unit_price
        FROM order_items oi
        JOIN books b ON b.book_id = oi.book_id
        WHERE oi.order_id IN ({placeholders})
        ORDER BY oi.order_id
    """
    conn = get_connection()
    try:
        rows = conn.execute(sql, order_ids).fetchall()
    finally:
        conn.close()
    return RetrievalResult(
        source="order_items",
        query=f"order_id IN ({', '.join(map(str, order_ids))})",
        records=rows_to_dicts(rows),
    )


def search_books(keyword: str | None = None,
                 genre: str | None = None,
                 author: str | None = None) -> RetrievalResult:
    """Search the catalogue by title keyword, genre, and/or author."""
    clauses, params, described = [], [], []
    if keyword:
        clauses.append("LOWER(title) LIKE '%' || LOWER(?) || '%'")
        params.append(keyword); described.append(f"title~'{keyword}'")
    if genre:
        clauses.append("LOWER(genre) = LOWER(?)")
        params.append(genre); described.append(f"genre={genre}")
    if author:
        clauses.append("LOWER(author) LIKE '%' || LOWER(?) || '%'")
        params.append(author); described.append(f"author~'{author}'")

    where = " AND ".join(clauses) if clauses else "1=1"
    sql = f"SELECT * FROM books WHERE {where} ORDER BY title"
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return RetrievalResult(
        source="books",
        query=" AND ".join(described) if described else "all books",
        records=rows_to_dicts(rows),
    )


def count_orders(date_from: str | None = None,
                 date_to: str | None = None) -> RetrievalResult:
    """Aggregate: how many orders (and total revenue) in a date range."""
    clauses, params, described = [], [], []
    if date_from:
        clauses.append("order_date >= ?"); params.append(date_from)
        described.append(f"date>={date_from}")
    if date_to:
        clauses.append("order_date <= ?"); params.append(date_to)
        described.append(f"date<={date_to}")
    where = " AND ".join(clauses) if clauses else "1=1"
    sql = f"""
        SELECT COUNT(*) AS order_count,
               COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM orders WHERE {where}
    """
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    record = {"order_count": row["order_count"],
              "total_revenue": round(row["total_revenue"], 2)}
    return RetrievalResult(
        source="orders",
        query=f"COUNT/SUM WHERE {' AND '.join(described) if described else 'all orders'}",
        records=[record],
    )


# --------------------------------------------------------------------------- #
# Unstructured-data tool (documents)
# --------------------------------------------------------------------------- #
def _load_documents() -> list[dict]:
    """Read every policy/company document into memory (text files + PDFs)."""
    docs = []
    if not DOCS_DIR.exists():
        return docs
    for path in sorted(DOCS_DIR.iterdir()):
        if path.suffix.lower() in (".txt", ".md"):
            text = path.read_text(encoding="utf-8")
        elif path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception:
                text = ""
        else:
            continue
        docs.append({"name": path.name, "text": text})
    return docs


# Very common words carry no meaning for document search. With only a handful
# of documents, keyword statistics are coarse, so we drop these from the *query*
# to stop words like "what/is/the" from dominating the ranking. (The documents
# themselves are indexed in full.)
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "do", "does", "did",
    "i", "you", "we", "they", "it", "what", "which", "who", "how", "when",
    "where", "why", "to", "of", "in", "on", "at", "for", "and", "or", "my",
    "me", "our", "your", "that", "this", "with", "about", "can", "could",
    "would", "please", "have", "has", "had", "get", "got", "tell", "show",
    "list", "give", "there", "your", "any",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _best_snippet(text: str, query_tokens: list[str], width: int = 240) -> str:
    """Return a clean excerpt centred on the first keyword hit.

    Whitespace is collapsed and the excerpt is trimmed to whole words, so it
    never cuts a word in half — much nicer to read in the answer.
    """
    collapsed = " ".join(text.split())            # normalise newlines/spacing
    lower = collapsed.lower()

    hits = [pos for pos in (lower.find(t) for t in query_tokens) if pos != -1]
    first_hit = min(hits) if hits else -1

    if first_hit == -1:
        start, end = 0, min(len(collapsed), width)
    else:
        start = max(0, first_hit - width // 3)
        end = min(len(collapsed), start + width)

    excerpt = collapsed[start:end]
    prefix = "... " if start > 0 else ""
    suffix = " ..." if end < len(collapsed) else ""

    # Drop any partial word left at a trimmed edge.
    if prefix and " " in excerpt:
        excerpt = excerpt.split(" ", 1)[1]
    if suffix and " " in excerpt:
        excerpt = excerpt.rsplit(" ", 1)[0]

    return f"{prefix}{excerpt.strip()}{suffix}"


def search_documents(query: str, top_k: int = 2) -> RetrievalResult:
    """Keyword-rank the documents against the query and return the best matches."""
    docs = _load_documents()
    all_tokens = _tokenize(query)
    # Prefer meaningful tokens; fall back to all tokens if nothing is left.
    query_tokens = [t for t in all_tokens if t not in _STOPWORDS] or all_tokens
    if not docs or not query_tokens:
        return RetrievalResult(source="documents",
                               query=f"keywords={query_tokens}", records=[])

    # Keyword-frequency scoring: for each document, count how often the query's
    # meaningful terms appear. Simple, exact, and predictable — the right choice
    # for a small document set (unlike BM25, whose corpus statistics are unstable
    # when there are only a handful of documents).
    scores = [sum(_tokenize(d["text"]).count(t) for t in query_tokens) for d in docs]
    ranked = sorted(zip(docs, scores), key=lambda p: p[1], reverse=True)
    records = []
    for doc, score in ranked[:top_k]:
        if score <= 0:
            continue
        records.append({
            "document": doc["name"],
            "score": round(float(score), 3),
            "snippet": _best_snippet(doc["text"], query_tokens),
        })
    return RetrievalResult(
        source="documents",
        query=f"keywords={query_tokens}",
        records=records,
    )
