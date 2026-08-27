"""
Load the raw data files (JSON + CSV) into a SQLite database.

This is the bridge between "a folder of files" (what the assignment asks for)
and "a queryable database" (what makes retrieval fast, exact, and demonstrable).
We ship the files AND load them into SQLite at setup time — best of both worlds.

Run from the backend/ folder:
    python -m scripts.load_data

It will (re)create backend/app/bookstore.db from scratch every time, so it is
safe to run repeatedly.
"""
import csv
import json
import sqlite3

from app.config import DATA_DIR, DB_PATH

# The schema is written out explicitly (rather than inferred) so the data types
# and relationships are clear to anyone reading the code.
SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT,
    city         TEXT,
    signup_date  TEXT,
    segment      TEXT
);

CREATE TABLE books (
    book_id  INTEGER PRIMARY KEY,
    title    TEXT NOT NULL,
    author   TEXT,
    genre    TEXT,
    price    REAL,
    stock    INTEGER,
    isbn     TEXT
);

CREATE TABLE employees (
    employee_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    role         TEXT,
    department   TEXT,
    hire_date    TEXT
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL,
    order_date    TEXT NOT NULL,
    status        TEXT,
    total_amount  REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id    INTEGER NOT NULL,
    book_id     INTEGER NOT NULL,
    quantity    INTEGER NOT NULL,
    unit_price  REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (book_id)  REFERENCES books(book_id)
);
"""


def read_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(name: str) -> list[dict]:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def insert(conn, table: str, rows: list[dict]):
    """Generic insert: build a parameterised query from the row keys."""
    if not rows:
        return
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    col_list = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])


def main():
    # Make sure the raw files exist; if not, generate them first.
    if not (DATA_DIR / "books.json").exists():
        print("Raw data not found — generating it first...")
        from scripts.generate_data import main as generate
        generate()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)

        insert(conn, "customers", read_json("customers.json"))
        insert(conn, "books", read_json("books.json"))
        insert(conn, "employees", read_json("employees.json"))
        insert(conn, "orders", read_csv("orders.csv"))
        insert(conn, "order_items", read_csv("order_items.csv"))

        conn.commit()

        # Report what we loaded, as a sanity check.
        for table in ("customers", "books", "employees", "orders", "order_items"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:12s}: {count} rows")
        print("Database built at", DB_PATH)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
