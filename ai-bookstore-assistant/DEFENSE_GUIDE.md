# Kamiya Bookstore — Project Defense Guide

Your complete prep for explaining and defending this project. Everything here is
grounded in the actual code. Companion docs: `PROJECT_DEFENSE.md` (the one-pager),
`ARCHITECTURE.md` (the diagrams), `TESTING.md`, `DEMO.md`.

**Golden rule when you speak:** the AI only *understands the question* and *words
the answer*. Your own Python does *all the data lookup*. That one sentence answers
half the hard questions.

---

## 1. What I actually built (by component)

- **Frontend (React + TypeScript, Vite, Tailwind).** A two-panel web page: a chat
  box for the question + answer, and a live "System Architecture / Execution
  Trace" panel. Files: `frontend/src/api.ts`, `App.tsx`, `components/*`.
- **Backend (Python + FastAPI, Uvicorn).** One streaming endpoint that runs the
  pipeline and streams results. Files: `backend/app/main.py`, `orchestrator.py`.
- **AI/LLM layer.** A swappable interface with a deterministic stub and an
  OpenAI-compatible implementation. Files: `llm.py`, `llm_openai.py`.
- **Data layer.** SQLite database (built from JSON/CSV) + policy text documents.
  Files: `retrieval.py`, `db.py`, `scripts/load_data.py`, `data/`.
- **Execution trace.** A `Tracer` that emits structured events at each real step.
  File: `events.py`.
- **Configuration.** One file for paths + LLM settings, secrets from `.env`.
  File: `config.py`.

---

## 2. Technology stack (verified from the code)

| Technology | Where used | What it does here | Why we use it | Alternative |
|---|---|---|---|---|
| **Python** | backend | all server logic | great for data + AI, fast to write | Node, Go |
| **FastAPI** | `main.py` | the web API + streaming | async-native (needed for SSE), tiny boilerplate | Flask, Django |
| **Uvicorn** | run command | runs the FastAPI app | the standard ASGI server for FastAPI | Hypercorn |
| **Pydantic** | `main.py` (`AskRequest`) | validates the request body | catches bad input automatically | manual checks |
| **SQLite** | `bookstore.db` | stores the structured data | zero-setup single file, real SQL | PostgreSQL, MySQL |
| **openai** (lib) | `llm_openai.py` | talks to the LLM | official client, OpenAI-compatible | raw HTTP |
| **python-dotenv** | `config.py` | loads `.env` (API key) | keeps secrets out of code | OS env vars |
| **pypdf** | `retrieval.py` | reads text from PDFs | supports PDF policy docs (none present yet) | pdfminer |
| **pytest** | `tests/` | runs the 22 tests | simple, standard | unittest |
| **React 18** | frontend | the UI that updates live | component + state model fits a live trace | Vue, Svelte |
| **TypeScript** | frontend | typed frontend code | catches mistakes; the event shape is a contract | plain JS |
| **Vite** | frontend | dev server + build | fast, modern default | Create-React-App |
| **Tailwind CSS** | frontend | styling | quick, consistent styling | plain CSS |

**"Why did you use X?" one-liners:**
- *FastAPI:* "It's async out of the box, which I needed for streaming the trace, and it's very little code."
- *SQLite:* "The data is relational and small, so a single-file database with real SQL was the simplest thing that actually works."
- *React + TS:* "The trace updates constantly, which is exactly what React's state model is for, and TypeScript keeps the event shape consistent with the backend."
- *OpenAI:* "It's a reliable, well-documented model; I put it behind an interface so it's swappable and optional."

---

## 3. Programming languages

- **Python** — the whole backend: the API, the pipeline, retrieval, the trace, the LLM calls.
- **TypeScript** — the whole frontend: sending the question, reading the stream, drawing the trace.
- **SQL** — the actual database queries inside `retrieval.py`.
- **HTML/CSS** — via Tailwind classes and `index.html`.

**"Why Python?"** — "It's the natural language for data and AI work, it has great libraries, and FastAPI made the backend quick to build."
**"Why TypeScript?"** — "The frontend and backend pass structured events back and forth; typing them means the two sides can't drift out of sync."
**"Why not one language for everything?"** — "Each side uses the best tool: Python is strongest for the data/AI backend, and React/TypeScript is the standard for an interactive browser UI. They talk over HTTP, so the split costs nothing."

---

## 4. Tools I used

- **Languages:** Python, TypeScript, SQL.
- **Frameworks:** FastAPI (backend), React (frontend).
- **Libraries:** Pydantic, openai, python-dotenv, pypdf, pytest; Vite, Tailwind, PostCSS.
- **AI/LLM service:** OpenAI API (optional, via `openai`).
- **Dev tools:** `pip` + a Python virtual environment; `npm`; Uvicorn (run the API); Vite (run/build the UI); pytest (tests).
- **Version control:** *Not set up yet — there is no git repo.* (Honest answer: "I'd `git init` and push to GitHub; I've been iterating locally.")
- **Data tools:** SQLite (via Python's built-in `sqlite3`).
- **Deployment/hosting:** None — it runs locally. (PoC, not deployed.)

One-sentence "what did I use this for": *Uvicorn runs my API; Vite runs and builds my frontend; pytest proves the retrieval and pipeline behave; python-dotenv keeps my API key out of the code.*

---

## 5. Architecture — what each part does

| Component | Responsibility | Technology | Key files | Input | Output |
|---|---|---|---|---|---|
| Frontend | collect question, show answer + trace | React/TS | `api.ts`, `App.tsx` | user's question | HTTP request; rendered UI |
| API endpoint | receive request, stream results | FastAPI | `main.py` | JSON `{question}` | SSE stream |
| Orchestrator | run the 4-step pipeline, emit events | Python | `orchestrator.py` | question | answer + events |
| LLM layer | understand question, word answer | stub/openai | `llm.py`, `llm_openai.py` | question / retrieved rows | intent+entities / answer text |
| Retrieval | run the real queries | Python + SQL | `retrieval.py` | ids/filters | records + the query it ran |
| Data | store the data | SQLite + files | `bookstore.db`, `data/` | SQL / keywords | rows / document snippets |
| Tracer | build trace events | Python | `events.py` | step info | `TraceEvent` objects |

---

## 6. One request, end to end — "What books did Nguyen Van A buy in July?"

| # | File · function | What happens | In → Out |
|---|---|---|---|
| 1 | `api.ts :: askQuestion()` | POSTs the question, opens the stream | question → HTTP request |
| 2 | `main.py :: ask()` | receives it, starts the pipeline on a background thread, returns an SSE stream | `{question}` → stream |
| 3 | `orchestrator.py :: run_query()` | runs analyze→select→retrieve→synthesize; emits events | question → answer + events |
| 4 | `llm.py :: StubLLM.analyze()` *(or OpenAI)* | classifies intent + extracts entities | question → `intent=order_history`, name, July dates |
| 5 | `orchestrator.py :: _select_sources()` | picks the sources for that intent | intent → `[customers, orders, order_items]` |
| 6 | `retrieval.py :: find_customer()` | SQL by name | "Nguyen Van A" → `customer_id 1001` |
| 7 | `retrieval.py :: search_orders()` | SQL by id + date range | 1001, July → orders `5007, 5012` |
| 8 | `retrieval.py :: get_order_items()` | SQL join to books | `[5007,5012]` → 4 book line items |
| 9 | `llm.py :: StubLLM.synthesize()` *(or OpenAI)* | words the answer from those rows only | rows → answer text |
| 10 | `main.py :: event_stream()` | streams the `answer` event then `done` | events → SSE |
| 11 | `App.tsx` + `TracePanel` | renders answer + the trace nodes | events → UI |

Meanwhile, **every step 3–9 emitted a trace event** as it happened.

---

## 7. Execution trace — how to defend it

**Lifecycle:** real step → `Tracer.step()`/`mark()` builds a `TraceEvent` →
`on_event` callback → `queue.Queue` → `event_stream()` writes it as an SSE message
(`main.py`) → `api.ts` reads it → `App.tsx :: reduceEvent()` updates React state →
`TracePanel`/`TraceNode` draw it.

**Event shape (`events.py`):** `seq, phase, label, status, started_at, source,
query, records_found, duration_ms, detail`.

**"How do you know the trace is real, not a hard-coded animation?"**
> "Because the events are emitted from *inside* the pipeline as each step runs —
> `Tracer.step()` literally wraps the real function call. The query text and record
> count on each event come straight from the actual database result. And the
> frontend has no fixed list of steps — it just draws whatever events arrive. If a
> customer isn't found, you see a real 'zero records' then a 'not found' event,
> because that's what actually happened."

**The one honest caveat (say it before they find it):** there's an optional pause
between events (`SSE_STEP_DELAY_MS`, default 250 ms) so a human can watch them
stream. It only changes *when* an event is sent — it never fabricates a step, and
the durations shown are the real measured timings. Set it to 0 and the same real
events stream instantly.

---

## 8. Who does what (LLM vs app vs retrieval vs frontend)

| Job | Who does it |
|---|---|
| Understand the question (intent + entities) | **LLM** (`analyze`) — or the stub |
| Decide which data sources to use | **App** (`_select_sources`, deterministic) |
| Run the actual queries | **Retrieval** (`retrieval.py`, SQL) |
| Access the data | **Retrieval → SQLite / documents** |
| Generate trace events | **App** (`Tracer` in `events.py`) |
| Word the final answer | **LLM** (`synthesize`) — from retrieved rows only |
| Show answer + trace | **Frontend** |

**What OpenAI does NOT do:** it does not query the database, does not choose tools,
does not run an autonomous loop, and does not decide what data exists. **Where
hallucination could happen:** only in the wording step — and it's contained because
the model is given *only* the retrieved rows and told to say "not found" otherwise,
and "not found" cases are answered by the app *before* the model is even called.

---

## 9. Data retrieval — "how does your AI actually search the data?"

> "It doesn't — my application does. The model turns the question into an intent
> and some entities. Then my Python picks the data sources and runs real SQL
> queries against a SQLite database. For 'what did this customer buy in July', it
> looks the name up to get a customer id, filters orders by that id and the date
> range, then joins those orders to the books. For policy questions it does a
> keyword search over the text documents instead. There's no vector search or
> embeddings — the data is relational, so exact SQL is the right tool."

Actual chain: `find_customer('Nguyen Van A')` → id `1001`; `search_orders(1001, July)`
→ orders `5007, 5012`; `get_order_items([5007,5012])` → 4 books. Each returns the
rows **and** the query string it ran (so the trace can show it).

---

## 10. Why I designed it this way (major decisions)

For each: **Q → natural answer → technical reason → trade-off → alternative → why reasonable.**

**Separate frontend & backend.**
*Answer:* "The browser UI and the data/AI logic are different jobs, so I split them; they talk over HTTP."
*Technical:* clean boundary, independent testing, standard web shape.
*Trade-off:* two things to run instead of one. *Alternative:* one server rendering HTML. *Why reasonable:* it's the normal, expected structure and made the streaming clean.

**Hybrid AI (LLM at the edges, deterministic retrieval in the middle).**
*Answer:* "The model is only for the fuzzy parts — reading the question and wording the answer. The data access is plain code, so results are exact and repeatable."
*Technical:* determinism where correctness matters; no hallucinated data; honest trace. *Trade-off:* less "magic", more explicit code. *Alternative:* let the model call tools itself. *Why reasonable:* for a demo that must be trustworthy and reproducible, this is safer and clearer.

**SQLite + real SQL (not a vector DB).**
*Answer:* "The data is relational, so exact filters beat fuzzy similarity search, and the queries are showable in the trace."
*Trade-off:* no semantic matching. *Alternative:* Postgres, or a vector DB. *Why reasonable:* simplest thing that's correct at this scale; the brief said avoid unnecessary complexity.

**Server-Sent Events (not WebSockets).**
*Answer:* "The trace only flows one way, server to browser, so I used SSE — it's simpler than WebSockets."
*Trade-off:* one-directional only. *Alternative:* WebSockets. *Why reasonable:* matches the exact need.

**Optional LLM with a deterministic stub.**
*Answer:* "It runs a deterministic stand-in by default so the demo always works and needs no key; add a key and it uses OpenAI."
*Trade-off:* stub's language is templated. *Alternative:* require a key. *Why reasonable:* reproducible demos + no secret needed to run.

**Config in one file, secrets in `.env`.**
*Answer:* "All paths and settings live in `config.py`, and the API key comes from a `.env` file that isn't committed."
*Why reasonable:* standard, safe, one place to change things.

---

## 11. "Why not something else?"

- **Why not a local LLM?** "OpenAI was reliable and zero-setup for a demo. A local model (Ollama) is possible — my interface is OpenAI-compatible, so I could point it at one — but it's heavier to run. Trade-off: cost/privacy vs setup effort."
- **Why FastAPI not Flask?** "FastAPI is async-native, which I needed for streaming; Flask would need extra work for that."
- **Why SQLite not PostgreSQL?** "Single file, zero setup, perfect for a PoC. Postgres is what I'd move to for multi-user production."
- **Why not RAG / a vector database?** "RAG is for unstructured, semantic search. My data is structured, so SQL is exact and simpler. I only keyword-search the few text documents."
- **Why not an agent / tool-calling?** "I wanted deterministic, observable behavior. An autonomous agent is less predictable and harder to trace; my orchestrator decides the steps."
- **Why not microservices?** "It's one small app; microservices would be pure overhead."
- **Why not hard-code the trace?** "That would defeat the whole point — the trace has to reflect real execution, so I emit events from inside the pipeline."

---

## 12. Error handling (expected → actual → improvement)

| Situation | Actual behavior in code | Improvement for production |
|---|---|---|
| Empty question | `main.py` sends an `error` event ("Empty question.") | also return HTTP 400 |
| Customer doesn't exist | `orchestrator` emits `NOT_FOUND` + a plain "couldn't find" answer, **no LLM call** | fuzzy-match suggestions |
| Real customer, no orders in range | `synthesize()` says "couldn't find any orders …" | same, fine |
| No matching document | `search_documents` returns empty → `NOT_FOUND` | broaden search |
| Database file missing | `db.get_connection()` raises a clear `FileNotFoundError` telling you to run `load_data` | auto-build on startup |
| A retrieval/tool error | `Tracer.step()` emits an `ERROR` event, then the error becomes a stream `error` — server doesn't crash | structured error codes |
| OpenAI call fails at request time | the exception propagates and becomes a stream `error` event *(not caught per-call)* | wrap the call, retry/fallback to stub |
| Can't build OpenAI client (bad/missing key) | `get_llm()` catches it and **falls back to the stub** | log a warning |
| Frontend can't reach backend | `api.ts` catches it → shows "Could not reach the server" | retry/backoff |

Honest note: a *failing OpenAI request mid-call* is surfaced as an error event but
not specifically retried or auto-downgraded to the stub — that's a real
improvement I'd make.

---

## 13. Security review (what's actually relevant)

- **API key:** read from `.env` via `config.py`; `.env` is in `.gitignore`. Good — but there's no git repo yet, so make sure `.env` is never added when you create one.
- **CORS:** `allow_origins=["*"]` in `main.py` — fine locally, too open for production; I'd restrict it to the real frontend origin.
- **Input validation:** Pydantic checks the request is `{question: str}`. Minimal but present.
- **SQL injection:** **not a risk** — all queries use parameterized placeholders (`?`), and the only string-built parts are fixed column/clause fragments, never user text.
- **Arbitrary file access:** **not a risk** — `search_documents` only reads from a fixed documents folder; the user can't supply a path.
- **Prompt injection:** a user could try to phrase a question to manipulate the *wording*, but the model only ever sees the retrieved rows, so it can't reach data it didn't retrieve. Low impact here.
- **Error messages:** raw `str(exception)` is sent to the client in error events — could leak internal detail; I'd sanitize these in production.
- **Auth / rate limiting:** none — acceptable for a local PoC, required for production.

---

## 14. Performance & scalability

- **10 users:** fine as-is.
- **1,000 users:** would need multiple Uvicorn workers and care around the per-request background thread; SQLite is okay for mostly-reads but starts to strain.
- **100,000 users:** move to PostgreSQL, run many stateless backend instances behind a load balancer, add caching and rate limiting.
- **1,000,000 users:** a proper streaming/queue layer instead of an in-memory queue, connection pooling, horizontal scaling, and a real observability stack.

**Current limits:** single process; one background thread + in-memory queue per
request; SQLite single file; no caching/pooling/rate-limiting. **What I'd change:**
real database, stateless horizontally-scaled backend, managed streaming, caching,
rate limiting, and metrics/logging around the trace.

---

## 15. "What did you actually do?" (honest)

> "I designed the architecture and built the whole thing end to end: the FastAPI
> backend, the retrieval layer over SQLite, the execution-trace system, the
> streaming, the LLM integration, and the React frontend that visualizes the
> trace. I used AI assistance to move faster while writing the code, but I was the
> one making the design decisions, integrating the pieces, testing it (22 tests),
> debugging real issues, and validating that it behaves correctly. I understand
> every part and can walk through any of it."

Two real debugging moments you can cite (they show maturity):
- A **Python version** issue: modern `int | None` type hints failed on Python 3.9; I fixed it with `from __future__ import annotations`.
- A **search-quality** issue: I first used BM25 for the documents, but with only a few files its statistics broke down and ranked the wrong doc; I switched to a simple, predictable keyword-frequency score — the right call at this scale.

---

## 16. Development story (supportable by the repo)

1. Understood the requirements (retrieval + **observable** trace). 2. Chose the
architecture (hybrid AI, SSE, SQLite). 3. Scaffolded backend + frontend. 4. Built
the mock dataset and loaded it into SQLite. 5. Built the deterministic retrieval
tools with tests. 6. Built the orchestrator + trace event model (with a stub LLM,
no key needed). 7. Added FastAPI + SSE streaming. 8. Added the OpenAI adapter. 9.
Built the React trace visualization + chat UI. 10. Wrote the test matrix (22
tests) and polished. 11. Wrote docs + diagrams.

---

## 17. DO NOT SAY (it would be inaccurate)

- ❌ "It uses RAG / embeddings / a vector database." → SQL + keyword search.
- ❌ "The LLM searches the database / picks the tools." → **My orchestrator** does.
- ❌ "It always uses OpenAI." → Only with a key; default is the stub.
- ❌ "It's an autonomous agent / does tool-calling / reasoning." → Fixed pipeline.
- ❌ "The trace is real-time to the millisecond." → It's real, but paced ~250 ms for viewing.
- ❌ "It's production-ready / scalable / secure." → It's a single-process PoC.
- ❌ "It's on GitHub / version-controlled." → No git repo yet.

---

## 18. Top questions the company may ask (with natural answers)

**Level 1 — Basic**
1. *What did you build?* → "An AI assistant over a mock bookstore that answers questions from its own data and shows a live trace of how it found the answer."
2. *What languages?* → "Python for the backend, TypeScript for the frontend, SQL for the queries."
3. *What's the frontend?* → "React with TypeScript, built with Vite, styled with Tailwind."
4. *What's the backend?* → "Python with FastAPI, run by Uvicorn."

**Level 2 — Code understanding**
5. *What happens when the user clicks Send?* → walk steps 1–11 from section 6, briefly.
6. *Which endpoint handles it?* → "`POST /api/ask` in `main.py`."
7. *Where's the data?* → "A SQLite database plus a few policy text files."
8. *How does the frontend talk to the backend?* → "It POSTs the question and reads a streaming response of trace events, then the answer."

**Level 3 — Architecture**
9. *Why separate frontend and backend?* → section 10.
10. *Why FastAPI?* → "Async-native for streaming, minimal code."
11. *Why SSE not WebSockets?* → "The trace only flows one way."
12. *Walk me through the architecture.* → use the `ARCHITECTURE.md` diagram.

**Level 4 — AI/LLM**
13. *What does the LLM actually do?* → "Two things only: understand the question and word the answer. It never touches the data."
14. *Are you using OpenAI?* → "It's built for it; it runs a deterministic stub by default and uses OpenAI when a key is set."
15. *Does it use tool-calling / an agent?* → "No — my orchestrator decides the steps; it's a fixed pipeline."
16. *How do you prevent hallucination?* → "The answer is built only from retrieved rows, and 'not found' cases are answered before the model is even called."

**Level 5 — Data retrieval**
17. *How does it search the data?* → section 9.
18. *Why not a vector database?* → "The data is relational; exact SQL is right and simpler."
19. *What are the data sources?* → "SQLite tables (customers, books, orders, order_items, employees) and policy text documents."

**Level 6 — Execution trace**
20. *What is the trace?* → "A structured, live record of each real step the system took."
21. *Where are events created?* → "Inside the pipeline, by the `Tracer` in `events.py`."
22. *How do they reach the browser?* → "They stream over Server-Sent Events; the frontend draws each one."
23. *How do you know it's real?* → section 7.

**Level 7 — Security**
24. *Where's the API key?* → "In a `.env` file that isn't committed; loaded via `config.py`."
25. *Any injection risk?* → "SQL is parameterized, so no SQL injection; document access is a fixed folder."

**Level 8 — Scalability**
26. *Would this scale?* → section 14 (be honest: PoC now, here's what I'd change).
27. *Biggest bottleneck?* → "The in-memory, single-process streaming and SQLite."

**Level 9 — Critical thinking**
28. *Weakest part?* → "The stub's language is templated, OpenAI-call failures aren't retried, and there's no auth — all fixable."
29. *What would you improve first for production?* → "A real database + auth + restricted CORS, then a managed streaming layer."
30. *What are you most confident about?* → "The trace design — it genuinely reflects real execution, which was the whole point of the assessment."

---

## 19. Rapid-fire (memorize the rhythm, not the words)

- Backend language? **Python.** · Why? **Data/AI + fast with FastAPI.**
- Framework? **FastAPI.** · Server? **Uvicorn.**
- Frontend? **React + TypeScript (Vite, Tailwind).**
- LLM? **OpenAI-compatible, optional; stub by default.**
- Where's the key? **`.env`, not committed.**
- What's `config.py`? **One place for paths + LLM settings.**
- Where's the data? **SQLite + text documents.**
- How retrieved? **Real SQL + keyword search.**
- Vector DB? **No.** · RAG? **No.** · Agent? **No.**
- What is the trace? **Live structured events of real steps.**
- Hard-coded trace? **No — emitted from the running pipeline.**
- Transport? **Server-Sent Events.**
- No data found? **Says "not found", doesn't invent.**
- API fails? **Becomes an error event; server stays up.**
- Endpoints? **`POST /api/ask`, `GET /api/health`.**
- Tests? **22, all passing.**
- Improve first? **Real DB + auth for production.**

---

## 20. Difficult questions (Q · short · deeper · follow-up)

**Q: If the LLM is optional, is this really an "AI" project?**
Short: "Yes — the AI does the language understanding and generation; the rest is deliberately deterministic so it's trustworthy."
Deeper: the assessment is about an *observable AI pipeline*; the hybrid design is the point, not a limitation.
Follow-up they may ask: *"So what breaks without the LLM?"* → "Nothing structurally — the stub still classifies and answers with templates; you lose natural phrasing and flexible understanding of messy questions."

**Q: How do you *guarantee* the answer only uses real data?**
Short: "The wording step is given only the retrieved rows, and 'not found' cases never reach the model."
Deeper: retrieval is separate from generation; there's no path for the model to fetch data itself.
Follow-up: *"Could the model still misquote a number?"* → "Possible in phrasing; I mitigate with a strict instruction and could add a citation check that every number maps to a retrieved row."

**Q: Your trace has a delay — isn't it fake then?**
Short: "The delay only spaces out *when* events are sent so a human can watch; the steps and durations are real. Set it to zero and the same events stream instantly."
Follow-up: *"Prove it's real."* → "Ask about a customer who doesn't exist — you'll see a real 'zero records' then 'not found', because that's what happened."

**Q: Why should I trust keyword search over the documents?**
Short: "At four documents, keyword frequency is exact and predictable; BM25's statistics actually broke down at that scale."
Follow-up: *"And at 10,000 documents?"* → "Then I'd switch to a proper index or embeddings — different scale, different tool."

**Q: What happens under concurrency?**
Short: "Each request runs on its own background thread with its own queue, so requests don't interfere; but it's single-process, so heavy load needs more workers."
Follow-up: *"Race conditions?"* → "Reads only, no shared mutable state per request, so no — but a shared write workload would need care."

---

## 21. "Explain my project in 60 seconds"

> "I built *Kamiya Bookstore* — an AI assistant over a mock online bookstore. The
> point isn't the chatbot; it's that you can watch the AI work. You ask something
> like 'what books did this customer buy in July,' and you get the answer on one
> side and a live, step-by-step trace of how the system found it on the other.
> It's a React front end and a Python FastAPI back end. When you ask, the back end
> runs a fixed four-step pipeline: analyze the question, pick the data sources,
> run the actual database queries, then word the answer from just those results.
> The data is a small SQLite database plus a few policy text files. The key choice
> is that the AI only understands the question and phrases the answer — all the
> real data lookup is deterministic Python and SQL, which keeps answers grounded
> and makes the trace trustworthy. Those trace steps stream to the browser live
> over Server-Sent Events. And it runs with no API key by default, so the demo is
> always reproducible."

## 22. "Explain my project in 3 minutes"

Same opening, then add: **architecture** (browser ↔ one FastAPI endpoint; pipeline
analyze→select→retrieve→synthesize) · **request flow** (name→id 1001, id+July→orders
5007/5012, orders→4 books) · **AI boundary** (LLM only analyzes + words; my code
retrieves) · **retrieval** (relational SQLite, real SQL; keyword search for docs;
no vector DB) · **trace** (emitted inside the pipeline, streamed via SSE, drawn by
React; real because events carry the actual query and record counts) · **tech**
(Python/FastAPI/Uvicorn/SQLite; React/TS/Vite/Tailwind; optional OpenAI) · **why it
makes sense** (simplest thing that's correct and observable) · **limits** (single-
process PoC, no auth, templated stub language) · **improvements** (real DB, auth,
restricted CORS, retry on LLM failure, managed streaming).

## 23. "What would you improve?" (mature answer)

> "For production I'd move SQLite to a real database like Postgres, add
> authentication and restrict CORS to the real frontend, and replace the in-memory
> streaming queue with a managed one so it scales across instances. On the AI side
> I'd wrap the OpenAI call so a failure retries or cleanly falls back to the stub,
> and I'd add a check that every fact in the answer maps to a retrieved record. And
> I'd put it under git with CI running the tests. None of these change the core
> design — they harden it."

---

## 24. "I know my project" checklist

- [ ] I can explain the project in 60 seconds.
- [ ] I can draw the architecture (browser → `/api/ask` → orchestrator → LLM + retrieval → SQLite/docs → SSE → browser).
- [ ] I know the languages (Python, TypeScript, SQL) and why.
- [ ] I know the frameworks (FastAPI, React) and why.
- [ ] I know the key libraries (Pydantic, openai, dotenv; Vite, Tailwind).
- [ ] I know the tools (Uvicorn, Vite, pytest, pip/venv, npm) — and that git isn't set up yet.
- [ ] I know where the LLM is used and, crucially, what it does NOT do.
- [ ] I can name the retrieval steps and the real filters (1001, 5007/5012, 4 books).
- [ ] I can name the important files and their jobs.
- [ ] I can explain the trace lifecycle and why it's real.
- [ ] I can explain what happens when data isn't found and when the API fails.
- [ ] I know the limitations and what I'd improve for production.
- [ ] I can answer "why X?" and "why not Y?" for every major choice.
- [ ] I can honestly describe my contribution and where AI assistance helped.
