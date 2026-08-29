# Kamiya Bookstore — AI Data Assistant

A proof-of-concept AI information-retrieval system for a mock online bookstore.
A user asks a natural-language question; an AI agent figures out which data it
needs, retrieves it from structured files (JSON/CSV → SQLite) and unstructured
documents (policies), and answers **only** from what it found. The signature
feature is a live **System Architecture / Execution Trace** panel that shows,
step by step, what the system is doing.

> Status: the full stack is in place — mock data, retrieval layer, orchestrator
> with a live execution trace, a FastAPI + SSE backend, an OpenAI-compatible LLM
> adapter (optional; a deterministic stub runs without a key), and a React UI.

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
│  ├─ .env.example         # copy to .env to enable a real LLM
│  ├─ app/
│  │  ├─ config.py         # paths, company name, LLM settings (one source of truth)
│  │  ├─ db.py             # SQLite connection helper
│  │  ├─ retrieval.py      # the deterministic retrieval "tools"
│  │  ├─ events.py         # the execution-trace event model + Tracer
│  │  ├─ llm.py            # LLM interface + deterministic stub + get_llm() factory
│  │  ├─ llm_openai.py     # real OpenAI-compatible implementation (optional)
│  │  ├─ orchestrator.py   # the analyze→select→retrieve→synthesize pipeline
│  │  └─ main.py           # FastAPI app: /api/health and streaming /api/ask (SSE)
│  ├─ scripts/
│  │  ├─ generate_data.py  # writes the mock data files (deterministic)
│  │  ├─ load_data.py      # loads the files into bookstore.db
│  │  └─ ask.py            # ask a question from the terminal, watch the trace
│  ├─ tests/               # retrieval, orchestrator, LLM, and API tests
│  └─ data/
│     ├─ books.json, customers.json, employees.json
│     ├─ orders.csv, order_items.csv
│     └─ documents/        # return-policy.txt, shipping-policy.txt, about-company.md, faq.txt
└─ frontend/
   ├─ package.json, vite.config.ts, tailwind.config.js, ...
   └─ src/
      ├─ App.tsx           # state + folds trace events into pipeline nodes
      ├─ api.ts            # fetch-based SSE client
      ├─ types.ts          # shared event types (mirrors backend)
      └─ components/       # Header, ChatPanel, TracePanel, TraceNode
```

## The mock data

An online bookstore, **Kamiya Bookstore** (Ho Chi Minh City): 15 books across 6
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
and the full backend suite pass (**22 tests**). See `TESTING.md` for the full
test matrix.

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

## (Optional) Use a real LLM

Without an API key, the app runs on a deterministic stub — perfect for a
reliable demo. To use a real model instead, copy `backend/.env.example` to
`backend/.env` and set your key:

```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

The app auto-detects the key on startup (`get_llm()` in `app/llm.py`). Nothing
else changes — the LLM only does query analysis and answer wording; all data
retrieval stays deterministic and grounded.

## Frontend (the web UI)

The UI is a React + TypeScript + Vite + Tailwind app in `frontend/`. From the
`frontend/` folder (with the backend already running):

```bash
npm install
npm run dev
```

Then open the URL it prints (default http://localhost:5173). It talks to the
backend at http://127.0.0.1:8000 — override with `VITE_API_BASE` in a
`frontend/.env` file if needed.

## Run the full app (quickstart)

Two terminals:

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # (Windows; use source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m scripts.load_data
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open the frontend URL, type a question (or click an example), and watch the
System Architecture panel light up step by step.

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
4. ✅ LLM integration (OpenAI-compatible, optional; stub fallback)
5. ✅ Execution-trace visualization (frontend)
6. ✅ Chat UI + end-to-end wiring
7. ✅ Test matrix + polish + demo script — see `TESTING.md` and `DEMO.md`
