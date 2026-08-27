"""
Database access helper.

We use SQLite because it is a single file with zero setup, yet it lets us run
*real* SQL queries — which is what makes the execution trace convincing (we can
show the actual query that ran, not "we looped over a JSON array").

`row_factory = sqlite3.Row` makes each row behave like a dict, so callers can do
row["title"] instead of dealing with positional tuples.
"""
import sqlite3

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a connection to the bookstore database with dict-like rows."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Run `python -m scripts.load_data` from the backend/ folder first."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows) -> list[dict]:
    """Convert sqlite3.Row objects into plain dicts (JSON-serializable)."""
    return [dict(r) for r in rows]
