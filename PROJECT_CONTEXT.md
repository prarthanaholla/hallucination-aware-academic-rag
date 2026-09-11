# Project Context — Hallucination-Aware Academic RAG (PESU CSE)

Read this file first if resuming work on this project in a new chat.

## What this project is

A RAG (retrieval-augmented generation) chatbot for PES University CSE
department data (courses, faculty, academic calendar). Its distinguishing
feature: every generated answer is split into sentences/clauses and each
one is checked against the retrieved source chunks using an NLI
(natural language inference) model, so the system can label its own
claims as verified, unverified, or an honest "I don't know" — instead
of just generating an answer and hoping it's right.

GitHub repo: https://github.com/prarthanaholla/hallucination-aware-academic-rag
(branch `main` — see "GitHub state" below, there's a leftover `master`
branch too that still needs manual cleanup on GitHub's side).

## Architecture

```
Backend/
  api/
    main.py              FastAPI app — routes: GET /health, POST /ask, GET /stats
    retriever.py          Pulls top-k chunks from ChromaDB for a query
    groq_generator.py     Calls Groq (llama-3.3-70b-versatile) to generate the answer
    sentence_verifier.py  Splits answer into units, NLI-verifies each against chunks
    response_builder.py   Assembles the final JSON response shape
  ingestion/
    extract_*.py          Pulls raw text from source PDFs (course catalog, faculty, calendar)
    chunk_*.py             Splits extracted data into retrievable chunks
    embed_and_store.py     Embeds chunks and writes them into Backend/data/chromadb/
  data/
    *.pdf, *.json          Source documents and extracted/chunked JSON
    chromadb/               The vector store (already built — don't need to re-run ingestion
                             unless you change the source PDFs)
  tests/
    eval_harness.py         Runs ~23 test questions (normal + adversarial) end-to-end,
                             prints per-question verdict + a summary
    debug_verification.py   Runs ONE query (edit QUERIES_TO_DEBUG at the top) and prints
                             the exact generated answer, retrieved chunks, and raw NLI
                             scores per verification unit — the main diagnostic tool
    debug_retrieval.py, smoke_test.py   other diagnostics
frontend/
  React + Vite + Tailwind app that talks to the backend's /ask endpoint
```

## How to run it

Backend (from `Backend/`):
```
pip install fastapi uvicorn groq chromadb sentence-transformers nltk torch transformers python-dotenv
```
Copy `Backend/.env.example` to `Backend/.env` and fill in your real `GROQ_API_KEY`
(the real key is NOT committed to git — only the placeholder example is).
```
uvicorn api.main:app --reload --port 8000
```

Frontend (from `frontend/`):
```
npm install
npm run dev
```
Runs at http://localhost:5173, CORS-allowed by the backend.

**Note:** there's no `requirements.txt` yet (see "Known gaps" below) —
dependencies are currently only listed as a comment at the top of `main.py`.

## What was fixed in the last session (chronological)

1. **Windows Unicode crash** — `main.py` had `print("🚀 ...")` at module import
   time. Windows' default console encoding (cp1252) can't render emoji, so the
   server crashed on startup before FastAPI even came up. Fixed by forcing
   UTF-8 stdout/stderr at the very top of `main.py` (before other imports).

2. **Verifier punished honest refusals** — Diagnosed via `debug_verification.py`
   on the query *"When will results be announced for even semesters?"*. The
   LLM correctly said "I don't have that information" (because the real
   results-announcement date sits in a PDF footer that `extract_calender.py`
   doesn't parse — it only parses the weekly table rows). But the verifier ran
   NLI on that refusal against an unrelated chunk, found no entailment, and
   mislabeled it `HALLUCINATED`. Fixed by adding a new `ABSTAINED` label:
   `sentence_verifier.py` now detects refusal phrases (regex patterns like
   "don't have that information", "not available in the knowledge base", etc.)
   and skips NLI verification for them entirely. Abstained units are also
   excluded from the numeric faithfulness score.

3. **Mixed abstain+claim answers could falsely reach TRUSTWORTHY** — Found via
   `eval_harness.py`: an answer with e.g. `[ABSTAINED, VERIFIED]` units scored
   100% (since only the VERIFIED unit counted), reaching `TRUSTWORTHY` even
   though part of the answer was "I don't know." Fixed with a cap: if an
   answer is a *partial* abstention (some units abstained, some not), the
   verdict can reach at most `MIXED`, never `TRUSTWORTHY`. Only an answer
   with zero abstained units can earn full `TRUSTWORTHY`.

   Both fixes verified against `eval_harness.py`'s 5 adversarial (no-real-answer)
   test questions: went from 4/5 correctly flagged to 5/5, with no regression
   on the 18 normal questions.

## Known open issues (NOT yet fixed — diagnosed but left for later)

- **`extract_calender.py` footer-parsing gap** — the actual results-announcement
  date lives in PDF footer text outside the weekly table structure the parser
  walks row-by-row. Confirmed via retrieval: no retrieved chunk ever contains
  that fact. Would need extending `extract_calender.py` to also capture footer
  text, then re-running the ingestion pipeline.

- **FAM 2 question intermittently mislabeled HALLUCINATED** — query: *"When is
  the FAM 2 (Faculty Advisor Meeting 2) for even semesters?"*. Sometimes scores
  `VERIFIED`/`TRUSTWORTHY` correctly; other times a factually-identical but
  differently-phrased answer (e.g. using "FAM 2" abbreviation and "even
  semesters" instead of the source chunk's "Faculty Advisor Meeting 2" and
  bracket notation `[2,4,6,8]`) gets scored `HALLUCINATED`. Root cause,
  confirmed with raw NLI scores: the small NLI model
  (`cross-encoder/nli-deberta-v3-small`) doesn't recognize the paraphrase as
  entailment (scores ~98% "neutral" instead), and the existing
  "lexical-overlap rescue" safety net (meant to catch exactly this) requires
  85% word overlap to fire — this case measured 80%, just under the bar,
  because of the two paraphrased words. Proposed but **not yet applied** fix:
  lower the overlap threshold (e.g. 0.85 → 0.75) or make the overlap
  calculation more tolerant of abbreviations/synonyms. This is also affected
  by **Groq's generation being non-deterministic** (no fixed temperature/seed),
  so the exact same question can produce different phrasing — and therefore a
  different verdict — on different runs. Not consistently reproducible.

- **No `requirements.txt` / `pyproject.toml`** — dependencies are only
  documented as a `pip install ...` comment inside `main.py`. Should be a
  real requirements file.

- **No `README.md`, no `LICENSE`** — repo has no top-level documentation or
  license file.

- **Binary vector DB committed to git** (`Backend/data/chromadb/*.bin`,
  `chroma.sqlite3`) — works, but non-standard; a production repo would
  usually regenerate this via the ingestion pipeline rather than committing
  binary index files.

- **`Backend/eval_results.json` committed** — looks like a generated test-run
  artifact rather than source; probably should be gitignored instead.

- **Groq free-tier rate limit** — 100,000 tokens/day. Heavy repeated testing
  (running `eval_harness.py`'s 23 questions many times in one session) can
  exhaust it. It's a rolling window, not a fixed midnight reset — capacity
  trickles back gradually rather than all at once.

## GitHub state

- Remote `origin` → `https://github.com/prarthanaholla/hallucination-aware-academic-rag.git`
- Local branch `main` tracks `origin/main`, single clean commit (no secrets,
  no `node_modules`, no `__pycache__`, no Claude co-author trailer — author
  is `prarthanaholla` only).
- **Unresolved GitHub-side cleanup**: GitHub still has `master` set as the
  repo's *default* branch (both `main` and `master` currently exist there
  with identical content, since `master` couldn't be deleted while it's
  default). To finish: go to Settings → Branches on GitHub, change the
  default branch to `main`, then delete `master`.
- The old messy 15-commit history (which included an accidental full
  `node_modules` commit) was replaced with one clean commit. It's preserved
  locally only, on branch `master-old-history` — never pushed anywhere.
- `Backend/.env` (real API key) is gitignored and was never committed;
  `Backend/.env.example` is committed as a placeholder template.
