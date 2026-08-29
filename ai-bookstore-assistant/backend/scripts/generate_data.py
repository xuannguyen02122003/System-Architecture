"""
Generate the mock dataset for "Kamiya Bookstore".

Why a generator instead of hand-written files?
  - The data is *curated and deterministic* (no randomness), so demo questions
    always return the exact same answer. That makes the app safe to demo.
  - The raw files it produces (JSON / CSV / TXT / MD) are committed to the repo,
    so the assignment's "a set of structured and unstructured files" requirement
    is satisfied with real files — this script just lets us regenerate them.

Run from the backend/ folder:
    python -m scripts.generate_data
"""
import csv
import json
from pathlib import Path

# We import config for the paths so there is a single source of truth.
from app.config import DATA_DIR, DOCS_DIR, COMPANY_NAME, COMPANY_TAGLINE

# --------------------------------------------------------------------------- #
# 1. BOOKS  (the product catalogue — category: books)
# --------------------------------------------------------------------------- #
BOOKS = [
    # id, title, author, genre, price, stock, isbn
    (1,  "The Silent Library",     "Ha Mai",           "Fiction",     12.50, 40, "978-1-01-000001"),
    (2,  "Quantum Mornings",       "Le Tran",          "Science",     18.00, 25, "978-1-01-000002"),
    (3,  "Saigon Rain",            "Nguyen Thi Lan",   "Fiction",      9.99, 60, "978-1-01-000003"),
    (4,  "The Data-Driven Mind",   "Pham Quoc",        "Technology",  25.00, 30, "978-1-01-000004"),
    (5,  "Little Star's Journey",  "Do Bich",          "Children",     7.50, 80, "978-1-01-000005"),
    (6,  "Empires of the Mekong",  "Tran Van Hung",    "History",     21.00, 20, "978-1-01-000006"),
    (7,  "Cooking with Lemongrass","Vu Thi Hoa",       "Non-Fiction", 16.00, 35, "978-1-01-000007"),
    (8,  "Deep Work Habits",       "Cao Minh",         "Non-Fiction", 14.00, 50, "978-1-01-000008"),
    (9,  "Neural Gardens",         "Le Tran",          "Science",     19.50, 15, "978-1-01-000009"),
    (10, "The Last Lantern",       "Ha Mai",           "Fiction",     11.00, 45, "978-1-01-000010"),
    (11, "Python for Analysts",    "Pham Quoc",        "Technology",  29.00, 22, "978-1-01-000011"),
    (12, "Whispers of Hue",        "Nguyen Thi Lan",   "Fiction",     10.50, 38, "978-1-01-000012"),
    (13, "Brave Little Boat",      "Do Bich",          "Children",     6.99, 90, "978-1-01-000013"),
    (14, "A Short History of Tea", "Tran Van Hung",    "History",     17.50, 28, "978-1-01-000014"),
    (15, "Mindful Money",          "Cao Minh",         "Non-Fiction", 15.50, 33, "978-1-01-000015"),
]

# --------------------------------------------------------------------------- #
# 2. CUSTOMERS
# --------------------------------------------------------------------------- #
CUSTOMERS = [
    # id, name, email, city, signup_date, segment
    (1001, "Nguyen Van A", "vana.nguyen@example.com",  "Ho Chi Minh City", "2025-03-14", "VIP"),
    (1002, "Tran Thi B",   "thib.tran@example.com",    "Hanoi",            "2025-06-02", "Regular"),
    (1003, "Le Van C",     "vanc.le@example.com",      "Da Nang",          "2026-01-20", "New"),
    (1004, "Pham Thi D",   "thid.pham@example.com",    "Ho Chi Minh City", "2024-11-11", "VIP"),
    (1005, "Hoang Van E",  "vane.hoang@example.com",   "Can Tho",          "2025-09-05", "Regular"),
    (1006, "Emily Carter", "emily.carter@example.com", "Singapore",        "2025-12-01", "Regular"),
    (1007, "Vo Thi F",     "thif.vo@example.com",      "Hue",              "2026-02-18", "New"),
    (1008, "Dang Van G",   "vang.dang@example.com",    "Nha Trang",        "2025-07-22", "Regular"),
    (1009, "Bui Thi H",    "thih.bui@example.com",     "Hai Phong",        "2024-08-30", "VIP"),
    (1010, "James Nguyen", "james.nguyen@example.com", "Sydney",           "2026-03-10", "New"),
]

# --------------------------------------------------------------------------- #
# 3. EMPLOYEES
# --------------------------------------------------------------------------- #
EMPLOYEES = [
    # id, name, role, department, hire_date
    (1, "Ngo Thi Mai",     "Store Manager",         "Management", "2024-02-01"),
    (2, "Truong Van Nam",  "Customer Support Lead", "Support",    "2024-05-15"),
    (3, "Ly Thi Oanh",     "Warehouse Coordinator", "Logistics",  "2025-01-10"),
    (4, "Phan Van Phuc",   "Data Analyst",          "Analytics",  "2025-08-01"),
    (5, "Dinh Thi Quyen",  "Marketing Specialist",  "Marketing",  "2025-03-20"),
    (6, "Mac Van Son",     "Support Agent",         "Support",    "2026-01-05"),
]

# --------------------------------------------------------------------------- #
# 4. ORDERS + their line items
#    Each entry: (order_id, customer_id, order_date, status, [(book_id, qty), ...])
#    Totals are computed from the book prices, so they are always consistent.
# --------------------------------------------------------------------------- #
ORDERS = [
    (5001, 1001, "2026-03-02", "Delivered",  [(1, 1)]),
    (5002, 1002, "2026-02-14", "Delivered",  [(12, 1)]),
    (5003, 1002, "2026-04-10", "Delivered",  [(3, 2)]),
    (5004, 1004, "2026-04-25", "Delivered",  [(6, 1)]),
    (5005, 1003, "2026-05-06", "Shipped",    [(5, 3)]),
    (5006, 1005, "2026-05-18", "Delivered",  [(7, 1)]),
    (5007, 1001, "2026-07-05", "Delivered",  [(4, 1), (11, 1)]),   # <- July, Nguyen Van A
    (5008, 1006, "2026-06-01", "Delivered",  [(2, 1)]),
    (5009, 1008, "2026-06-14", "Cancelled",  [(10, 1)]),
    (5010, 1009, "2026-06-29", "Delivered",  [(14, 2)]),
    (5011, 1007, "2026-07-02", "Delivered",  [(13, 2)]),
    (5012, 1001, "2026-07-19", "Shipped",    [(8, 2), (15, 1)]),   # <- July, Nguyen Van A
    (5013, 1010, "2026-07-25", "Processing", [(11, 1)]),
    (5014, 1004, "2026-08-01", "Delivered",  [(15, 1)]),
    (5015, 1003, "2026-01-15", "Delivered",  [(1, 1)]),
    (5016, 1009, "2026-08-20", "Shipped",    [(4, 1)]),
    (5017, 1005, "2026-03-30", "Delivered",  [(8, 1)]),
    (5018, 1006, "2026-05-22", "Delivered",  [(9, 2)]),
    (5019, 1001, "2026-08-08", "Processing", [(9, 1)]),
]

# Lookup so we can price line items.
PRICE_BY_BOOK = {b[0]: b[4] for b in BOOKS}


def build_records():
    """Turn the tuples above into dict records + computed order totals."""
    books = [
        {"book_id": b[0], "title": b[1], "author": b[2], "genre": b[3],
         "price": b[4], "stock": b[5], "isbn": b[6]}
        for b in BOOKS
    ]
    customers = [
        {"customer_id": c[0], "name": c[1], "email": c[2], "city": c[3],
         "signup_date": c[4], "segment": c[5]}
        for c in CUSTOMERS
    ]
    employees = [
        {"employee_id": e[0], "name": e[1], "role": e[2],
         "department": e[3], "hire_date": e[4]}
        for e in EMPLOYEES
    ]

    orders, order_items = [], []
    for oid, cid, date, status, items in ORDERS:
        total = 0.0
        for book_id, qty in items:
            unit = PRICE_BY_BOOK[book_id]
            total += unit * qty
            order_items.append({
                "order_id": oid, "book_id": book_id,
                "quantity": qty, "unit_price": round(unit, 2),
            })
        orders.append({
            "order_id": oid, "customer_id": cid, "order_date": date,
            "status": status, "total_amount": round(total, 2),
        })
    return books, customers, employees, orders, order_items


def write_json(path: Path, data: list[dict]):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, data: list[dict]):
    if not data:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


# --------------------------------------------------------------------------- #
# 5. Unstructured documents (policies / company info / FAQ)
# --------------------------------------------------------------------------- #
RETURN_POLICY = """KAMIYA BOOKSTORE - RETURN POLICY

We want you to love every book you buy from us.

1. RETURN WINDOW
   You may return most items within 30 days of the delivery date for a full
   refund to your original payment method.

2. CONDITION
   Books must be in original, resalable condition. Items marked as "Final Sale"
   and digital products (e-books, gift cards) cannot be returned.

3. HOW TO RETURN
   Email support@kamiya.example with your order number. We will send a
   prepaid return label within 2 business days.

4. REFUND TIMING
   Refunds are processed within 5 business days after we receive the returned
   item. Original shipping fees are non-refundable unless the item was damaged
   or incorrect.

5. DAMAGED OR WRONG ITEMS
   If your order arrives damaged or incorrect, contact us within 7 days and we
   will replace it at no cost.
"""

SHIPPING_POLICY = """KAMIYA BOOKSTORE - SHIPPING POLICY

DELIVERY TIMES
  - Ho Chi Minh City & Hanoi: 1-2 business days
  - Other cities in Vietnam:   2-4 business days
  - International:              7-14 business days

SHIPPING COST
  - Standard shipping: 30,000 VND flat rate within Vietnam.
  - FREE standard shipping on all domestic orders over 300,000 VND.
  - International shipping is calculated at checkout by destination.

ORDER PROCESSING
  Orders placed before 3:00 PM (ICT) on a business day are processed the same
  day. Orders placed later, or on weekends/holidays, are processed the next
  business day.

TRACKING
  A tracking number is emailed once your order status changes to "Shipped".
"""

ABOUT_COMPANY = f"""# About {COMPANY_NAME}

{COMPANY_TAGLINE}

{COMPANY_NAME} was founded in 2024 as a small independent online bookstore. We
curate fiction, non-fiction, science, history, technology, and children's titles
from Vietnamese and international authors.

## Our mission
To make good books easy to find and affordable for every reader in Vietnam.

## By the numbers
- Founded: 2024
- Headquarters: Ho Chi Minh City, Vietnam
- Catalogue: 15+ curated titles across 6 genres
- Team: a small crew across Management, Support, Logistics, Analytics, and Marketing

## Contact
- Support: support@kamiya.example
- Hours: Monday to Friday, 9:00 AM - 6:00 PM (ICT)
"""

FAQ = """KAMIYA BOOKSTORE - FREQUENTLY ASKED QUESTIONS

Q: What payment methods do you accept?
A: We accept Visa, Mastercard, domestic ATM cards, MoMo, and cash on delivery
   (COD) for orders within Vietnam.

Q: Do you have a membership or loyalty program?
A: Yes. Customers are grouped into New, Regular, and VIP tiers based on order
   history. VIP customers receive early access to new titles and seasonal
   discounts.

Q: Can I change or cancel my order?
A: You can cancel an order for free while its status is "Processing". Once it is
   "Shipped", it can no longer be cancelled but may be returned (see the return
   policy).

Q: Do you ship internationally?
A: Yes, we ship worldwide. International delivery takes 7-14 business days.

Q: How do I track my order?
A: When your order status changes to "Shipped", we email you a tracking number.
"""


def write_documents():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "return-policy.txt").write_text(RETURN_POLICY, encoding="utf-8")
    (DOCS_DIR / "shipping-policy.txt").write_text(SHIPPING_POLICY, encoding="utf-8")
    (DOCS_DIR / "about-company.md").write_text(ABOUT_COMPANY, encoding="utf-8")
    (DOCS_DIR / "faq.txt").write_text(FAQ, encoding="utf-8")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    books, customers, employees, orders, order_items = build_records()

    # Structured data: a mix of JSON and CSV to satisfy the "multiple formats"
    # requirement (and to exercise different loaders later).
    write_json(DATA_DIR / "books.json", books)
    write_json(DATA_DIR / "customers.json", customers)
    write_json(DATA_DIR / "employees.json", employees)
    write_csv(DATA_DIR / "orders.csv", orders)
    write_csv(DATA_DIR / "order_items.csv", order_items)

    # Unstructured data: policy + company documents.
    write_documents()

    print("Generated dataset in", DATA_DIR)
    print(f"  books={len(books)} customers={len(customers)} "
          f"employees={len(employees)} orders={len(orders)} "
          f"order_items={len(order_items)}")
    print("  documents: return-policy.txt, shipping-policy.txt, "
          "about-company.md, faq.txt")


if __name__ == "__main__":
    main()
