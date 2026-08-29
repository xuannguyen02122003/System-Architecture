# Project Defense Cheat Sheet — Chapter One Books · AI Data Assistant

*Read this in 2 minutes before talking to the company. Every line is grounded in
the actual code.*

## Project purpose
Make an AI data-retrieval system **observable**. A user asks a natural-language
question about a mock online bookstore; the app answers **from its own data** and
shows a **live, step-by-step trace of exactly what it did** to get there. The real
target of the assessment is that visible execution trace — not the chatbot.

## What I built (say this)
A full-stack web app: a **React + TypeScript** frontend and a **Python + FastAPI**
backend. The backend runs a fixed four-step pipeline — **analyze → select sources
→ retrieve → synthesize** — over a small **SQLite** database and some text policy
documents. As it runs, it emits **structured trace events** that stream live to the
browser over **Server-Sent Events** and render as an animated pipeline. The **LLM
is used only to understand the question and to word the answer**; all data
retrieval in the middle is deterministic Python, which keeps answers grounded and
makes the trace trustworthy.

## Languages
**Python** (backend), **TypeScript** (frontend), **SQL** (the database queries),
and HTML/CSS via **Tailwind**.

## Frontend
**React 18 + TypeScript**, built with **Vite**, styled with **Tailwind CSS**.
Key files: `src/api.ts`, `src/App.tsx`, `src/components/{ChatPanel,TracePanel,TraceNode,Header}.tsx`.

## Backend
**Python + FastAPI**, served by **Uvicorn**. **Pydantic** validates the request
body (`AskRequest`). Key files: `app/main.py`, `orchestrator.py`, `events.py`,
`retrieval.py`, `llm.py`, `llm_openai.py`, `db.py`, `config.py`.

## AI / LLM
OpenAI-compatible, via the official **`openai`** Python library (`llm_openai.py`).
**Important and true:** OpenAI is used **only if `OPENAI_API_KEY` is set**;
otherwise the app runs a deterministic **`StubLLM`** with no network call. The LLM
does exactly two things: `analyze()` the question → intent + entities, and
`synthesize()` the answer from the retrieved rows. It never touches the database.

## Data
A **SQLite** database `bookstore.db` with tables **customers, books, orders,
order_items, employees**, built from JSON/CSV files by `scripts/load_data.py`.
Plus **policy documents** (`.txt`/`.md`) searched by keyword. Retrieval = **real
SQL** for structured data + **keyword-frequency search** for documents.
**No vector database, no embeddings, no RAG.**

## Architecture (components)
`Frontend (React)` → `FastAPI endpoint POST /api/ask` → `Orchestrator (run_query)`
→ `{ LLM (stub/OpenAI) , Retrieval tools → SQLite + documents }` → `Tracer` →
`SSE stream` → back to the `Frontend`. Endpoints: **`POST /api/ask`** (streaming)
and **`GET /api/health`**.

## Execution trace (the centerpiece)
A structured record of what the system actually did. **Created inside the pipeline**
by a `Tracer` (`events.py`) at each real step; each event carries `phase`, `status`,
`source`, `query`, `records_found`, `duration_ms`, `timestamp`. It streams live to
the browser via SSE, and the frontend folds each `running → completed` pair into a
visual node. It's **real** because the events are emitted from the actual running
code with the real query and record counts — not a pre-written script.

## Tools
Python + `pip` + virtual environment; Node + `npm`; **Uvicorn** (runs the API);
**Vite** (runs/builds the frontend); **pytest** (22 tests); the **OpenAI API**
(optional). Editor/OS: *(your VS Code on Windows)*. **Version control: not set up
yet — no git repo.** *(Honest gap; easy to add and worth mentioning.)*

## Important files (12)
| File | What it does |
|---|---|
| `backend/app/main.py` | FastAPI server; `POST /api/ask` streams the trace + answer (SSE) |
| `backend/app/orchestrator.py` | The pipeline `run_query()`: analyze→select→retrieve→synthesize |
| `backend/app/events.py` | The trace engine: `Tracer`, `TraceEvent` |
| `backend/app/retrieval.py` | Deterministic data tools (SQL + document search) |
| `backend/app/llm.py` | LLM interface, `StubLLM`, `get_llm()` selector |
| `backend/app/llm_openai.py` | Real OpenAI implementation (optional) |
| `backend/app/db.py` | Opens the SQLite connection |
| `backend/app/config.py` | All paths + LLM settings in one place |
| `backend/scripts/load_data.py` | Builds `bookstore.db` from JSON/CSV |
| `frontend/src/api.ts` | Sends the question, reads the SSE stream |
| `frontend/src/App.tsx` | Holds state, folds events into trace nodes |
| `frontend/src/components/TracePanel.tsx` | Renders the live trace |

## Main data flow
```
User → api.ts (HTTP POST) → main.py /api/ask → orchestrator.run_query()
     → llm.analyze() → _select_sources() → retrieval.* (SQLite/docs)
     → llm.synthesize() → answer → SSE → App.tsx → screen
```

## Main trace flow
```
real backend step → Tracer.step()/mark() builds a TraceEvent
  → on_event callback → queue.Queue → SSE "trace" message (main.py)
  → api.ts onTrace() → App.tsx reduceEvent() → TracePanel/TraceNode render
```

## DO NOT SAY (it would be inaccurate)
- ❌ "It uses RAG / embeddings / a vector database." → It uses SQL + keyword search.
- ❌ "The LLM searches the database / decides which tools to call." → **My Python**
  (`orchestrator.py`) decides and runs the queries; the LLM only analyzes and words.
- ❌ "It always uses OpenAI." → Only with an API key; the default is the stub.
- ❌ "It's an autonomous agent / does tool-calling / reasoning." → It's a fixed,
  deterministic pipeline.
- ❌ "It's production-scalable / battle-tested." → It's a single-process PoC.
