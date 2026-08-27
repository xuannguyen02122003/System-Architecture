"""
Tests for the retrieval layer.

These double as living documentation of the demo scenarios: each test is one of
the questions we will ask the finished app, pinned to its expected data. If the
dataset ever drifts, these tests tell us before a live demo does.

Run from the backend/ folder:
    python -m pytest -v
"""
from app.retrieval import (
    find_customer, search_orders, get_order_items,
    search_books, count_orders, search_documents,
)


# --- Happy path: resolve a customer by (partial) name ---------------------- #
def test_find_customer_resolves_name():
    result = find_customer("Nguyen Van A")
    assert result.records_found == 1
    assert result.records[0]["customer_id"] == 1001
    assert result.records[0]["segment"] == "VIP"


def test_find_customer_not_found():
    result = find_customer("Taylor Swift")
    assert result.records_found == 0          # proves we don't invent people


# --- Multi-source path: "what books did customer 1001 buy in July?" -------- #
def test_july_orders_for_customer():
    orders = search_orders(customer_id=1001,
                           date_from="2026-07-01", date_to="2026-07-31")
    assert orders.records_found == 2
    order_ids = [o["order_id"] for o in orders.records]
    assert set(order_ids) == {5007, 5012}

    items = get_order_items(order_ids)
    titles = {r["title"] for r in items.records}
    assert titles == {
        "The Data-Driven Mind", "Python for Analysts",
        "Deep Work Habits", "Mindful Money",
    }


# --- Aggregation path: "how many orders in Q2 2026?" ----------------------- #
def test_count_orders_q2():
    result = count_orders(date_from="2026-04-01", date_to="2026-06-30")
    assert result.records[0]["order_count"] == 8
    assert result.records[0]["total_revenue"] > 0


# --- Catalogue search ------------------------------------------------------ #
def test_search_books_by_genre():
    result = search_books(genre="Science")
    titles = {b["title"] for b in result.records}
    assert titles == {"Quantum Mornings", "Neural Gardens"}


# --- Document (unstructured) path ------------------------------------------ #
def test_search_documents_return_policy():
    result = search_documents("return policy refund")
    assert result.records_found >= 1
    assert result.records[0]["document"] == "return-policy.txt"


def test_search_documents_no_match():
    result = search_documents("spaceship rocket propulsion")
    assert result.records_found == 0          # no relevant doc -> empty, not made up
