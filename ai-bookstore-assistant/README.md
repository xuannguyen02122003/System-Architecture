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
and **12 passing tests**.

## Try it in the terminal

You can ask a question right now — no web UI or API key needed yet — and watch
the execution trace print live:

```bash
python -m scripts.ask "What books did Nguyen Van A buy in July?"
```

Example output (abridged):

```
* [ 1] REQUEST_RECEIVED  User question received
  ok [ 3] QUERY_ANALYSIS    Analyze the question   ->  query=(intent = order_history)
  ok [ 7] DATA_RETRIEVAL    Look up customer 'Nguyen Van A'  ->  source=customers | records=1
  ok [ 9] DATA_RETRIEVAL    Search this customer's orders    ->  query=(customer_id=1001 AND date>=2026-07-01 AND date<=2026-07-31) | records=2
  ok [11] DATA_RETRIEVAL    Fetch the books in those orders  ->  source=order_items | records=4
* [14] COMPLETED         Response ready
ANSWER:   In July 2026, Nguyen Van A purchased: The Data-Driven Mind, Python for
Analysts, Deep Work Habits (x2), Mindful Money. (Orders #5007, #5012.)
```

This is the same pipeline (and the same trace events) the web app will use — the
frontend will just render these events as an animated diagram instead of text.

## Run the web API (backend server)

From the `backend/` folder with the venv active:

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints:

- `GET  /api/health` — liveness check.
- `POST /api/ask` — body `{"question": "..."}`; responds with a live
  **Server-Sent Events** stream of the execution trace, then an `answer` event.
- `GET  /docs` — FastAPI's auto-generated API explorer.

Watch the stream from the command line:

```bash
curl -N -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the return policy?"}'
```

You'll see `event: trace` messages arrive one by one (paced ~250ms apart for
visibility — set `SSE_STEP_DELAY_MS=0` to disable), then a final `event: answer`.

## Demo questions this dataset supports

| Question | Path exercised |
| --- | --- |
| "What books did Nguyen Van A buy in July?" | customer → orders → order_items (multi-source) |
| "How many orders were placed in Q2 2026?" | aggregation over structured data |
| "What is the return policy?" | unstructured document search |
| "What did Taylor Swift order?" | not-found (proves no hallucination) |

## Roadmap

1. ✅ Scaffold + mock dataset + retrieval layer (with tests)
2. ✅ Orchestrator + execution-event model (stub LLM, runs with no API key)
3. ✅ FastAPI server + SSE streaming of trace events
4. ⬜ LLM integration (OpenAI-compatible)
5. ⬜ Execution-trace visualization (frontend)
6. ⬜ Chat UI + end-to-end wiring
7. ⬜ Test matrix + polish + demo script
