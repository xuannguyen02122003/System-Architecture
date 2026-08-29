# Demo Guide

A 5-minute walkthrough for presenting the AI Data Assistant. The goal is to show
that this is **not** a black-box chatbot: you can see exactly how the system
finds each answer.

## Before the demo (one-time setup)

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m scripts.load_data
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open the frontend URL (usually http://localhost:5173). No API key is required —
the app runs on a deterministic engine so the demo is 100% reproducible.

> Tip: the trace is paced ~250 ms per step so it's easy to follow live. To slow
> it down further for a big screen, start the backend with
> `SSE_STEP_DELAY_MS=500`.

## The 30-second pitch

> "This is a small AI information-retrieval system over a mock bookstore. On the
> left you ask a question and get an answer. On the right you see the System
> Architecture panel — a live trace of exactly what the system did to find that
> answer: how it understood the question, which data sources it searched, the
> real queries it ran, how many records it found, and how long each step took.
> The answer is always grounded in real data — if it can't find something, it
> says so instead of making it up."

## Suggested question sequence

Run these in order; each one showcases a different capability.

**1. Multi-source retrieval — the flagship**
> *"What books did Nguyen Van A buy in July?"*

Point at the right panel as it streams: the system identifies the intent
(order history), selects three sources, resolves the **name → customer_id**,
filters **orders** by that id and the July date range, then joins to
**order_items** to get the titles. Note the real query on each node
(`customer_id=1001 AND date>=2026-07-01 …`) and the record counts. The answer
lists the exact books with order IDs, and the "Data sources used" chips confirm
it touched customers, orders, and order_items.

**2. Aggregation**
> *"How many orders were placed in Q2 2026?"*

Different shape: one source, a COUNT/SUM query, a single aggregated result. Shows
the system isn't just doing lookups.

**3. Unstructured documents**
> *"What is the return policy?"*

Now it searches the **documents** source (policy files) instead of the database,
and cites `return-policy.txt`. Shows structured *and* unstructured retrieval.

**4. Hallucination resistance — the money shot**
> *"What did Taylor Swift order?"*

The trace looks up the customer, finds **0 records**, and shows an amber
**Not found** node. The answer plainly says it couldn't find that customer. This
is the key trust point: no data, no invented answer.

**5. Out-of-scope question**
> *"Tell me a joke about penguins"*

The system recognizes it can't serve this and asks the user to rephrase — it
fails gracefully.

Optionally, click **Raw events** (top-right of the trace panel) to reveal the
structured JSON behind the visual — useful if a technical reviewer asks "what's
actually being emitted?".

## Design decisions worth mentioning

- **SQLite + real SQL, not a vector database.** The data is relational, so exact
  filters are the right tool — and they're *showable* in the trace. A vector DB
  would be slower to set up and fuzzier here.
- **Hybrid design.** The LLM only understands the question and phrases the
  answer; all data access is deterministic Python. That keeps results exact,
  repeatable, and safe to demo.
- **The trace is emitted by the real pipeline**, not scripted — so it can never
  disagree with what actually happened. Try the error case (stop the backend
  mid-demo) and the UI degrades gracefully.
- **Grounded answers.** The answer generator only ever sees retrieved records
  and is told to say "not found" otherwise; "not found" cases short-circuit
  before any answer is generated.

## Likely questions & answers

- *"Is it using a real LLM?"* — It can. By default it runs a deterministic stub
  so the demo is reproducible; set `OPENAI_API_KEY` in `backend/.env` and it uses
  a real OpenAI-compatible model for the same two steps (analysis + wording),
  with retrieval unchanged.
- *"Why no RAG / embeddings?"* — The data is structured; exact SQL beats semantic
  search here and is easier to explain and verify. Documents use simple keyword
  search, which is more reliable than BM25 at this small scale.
- *"Could it scale?"* — Yes: SQLite → Postgres, the document search → a real
  index, and the LLM step swaps in without touching the pipeline or the trace.
