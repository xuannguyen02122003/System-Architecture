# Chapter One Books — AI Data Assistant

A proof-of-concept AI information-retrieval system for a mock online bookstore.
A user asks a natural-language question; an AI agent figures out which data it
needs, retrieves it from structured files (JSON/CSV → SQLite) and unstructured
documents (policies), and answers **only** from what it found. The signature
feature is a live **System Architecture / Execution Trace** panel that shows,
step by step, what the system is doing.

> This README grows as the project is built. It currently documents the
> foundation (data + retrieval layer). Backend API, LLM, streaming, and UI
> follow in later stages.

## Why this design (the short version)

- **The data is relational**, so retrieval is real SQL over **SQLite**, not a
  vector database. This is exact, fast, and — importantly — *showable* in the
  trace (we display the actual query that ran).
- **Hybrid agent**: the LLM handles the fuzzy parts (understand the question,
  pick sources, write the final answer); deterministic Python does the actual
  data retrieval. This keeps results exact and repeatable for a live demo.
- **The trace is emitted by the real pipeline**, not scripted — so it can never
  lie about what happened.
- **No hallucination**: the answer is grounded strictly in retrieved records; if
  nothing is found, the system says so.

## Architecture

```
Frontend (React)  ──POST /api/ask──▶  Backend (FastAPI)
   Chat panel                          Orchestrator: analyze → select →
   Trace panel ◀──SSE event stream──   retrieve → synthesize
                                        Retrieval layer:
                                          SQLite (customers, books, orders...)
                                          + document keyword search (policies)
                                        LLM: OpenAI-compatible (swappable)
```

## Project structure

```
ai-bookstore-assistant/
├─ README.md
├─ backend/
│  ├─ requirements.txt
│  ├─ app/
│  │  ├─ config.py         # paths, company name, LLM settings (one source of truth)
│  │  ├─ db.py             # SQLite connection helper
│  │  └─ retrieval.py      # the deterministic retrieval "tools"
│  ├─ scripts/
│  │  ├─ generate_data.py  # writes the mock data files (deterministic)
│  │  └─ load_data.py      # loads the files into bookstore.db
│  ├─ tests/
│  │  └─ test_retrieval.py # pins the demo scenarios to expected data
│  └─ data/
│     ├─ books.json, customers.json, employees.json
│     ├─ orders.csv, order_items.csv
│     └─ documents/        # return-policy.txt, shipping-policy.txt, about-company.md, faq.txt
└─ (frontend/ — added in a later stage)
```

## The mock data

An online bookstore, **Chapter One Books** (Ho Chi Minh City): 15 books across 6
genres, 10 customers (New/Regular/VIP), 19 orders with line items, 6 employees,
and 4 policy/company documents. The data is curated so demo questions have exact,
repeatable answers.

## Setup (backend data layer)

From the `backend/` folder:

```bash
# 1. (recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. generate the data files and build the database
python -m scripts.load_data

# 4. run the tests to confirm everything works
python -m pytest -v
```

You should see the database build (`customers: 10 rows`, `books: 15 rows`, ...)
and **7 passing tests**.

## Demo questions this dataset supports

| Question | Path exercised |
| --- | --- |
| "What books did Nguyen Van A buy in July?" | customer → orders → order_items (multi-source) |
| "How many orders were placed in Q2 2026?" | aggregation over structured data |
| "What is the return policy?" | unstructured document search |
| "What did Taylor Swift order?" | not-found (proves no hallucination) |

## Roadmap

1. ✅ Scaffold + mock dataset + retrieval layer (with tests)
2. ⬜ Orchestrator + execution-event model (stub LLM, runs with no API key)
3. ⬜ SSE streaming of trace events
4. ⬜ LLM integration (OpenAI-compatible)
5. ⬜ Execution-trace visualization (frontend)
6. ⬜ Chat UI + end-to-end wiring
7. ⬜ Test matrix + polish + demo script
