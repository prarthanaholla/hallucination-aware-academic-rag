# ================================================================
# smoke_test.py
#
# Day 1: verify every piece of the pipeline actually works, in
# isolation and end-to-end, BEFORE building anything new.
#
# Checks each component separately so a failure tells you exactly
# where the problem is, instead of one big traceback from main.py.
#
# Usage:
#   python smoke_test.py
# ================================================================

import os
import sys
import traceback

CHECKS_PASSED = []
CHECKS_FAILED = []


def check(name):
    """Decorator-style helper: run a check, record pass/fail, keep going."""
    def decorator(fn):
        print(f"\n--- {name} ---")
        try:
            fn()
            print(f"  ✅ PASS")
            CHECKS_PASSED.append(name)
        except Exception as e:
            print(f"  ❌ FAIL: {e}")
            traceback.print_exc(limit=2)
            CHECKS_FAILED.append((name, str(e)))
    return decorator


# -------------------------------------------------------
# 1. Environment / config
# -------------------------------------------------------
@check("Environment: GROQ_API_KEY present")
def _():
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GROQ_API_KEY", "")
    assert key, "GROQ_API_KEY not set in .env"
    assert key.startswith("gsk_"), "GROQ_API_KEY doesn't look like a valid Groq key"


# -------------------------------------------------------
# 2. Data files exist
# -------------------------------------------------------
@check("Data files: chunk files exist")
def _():
    required = [
        "data/chunks_courses.json",
        "data/chunks_faculty.json",
        "data/chunks_calendar.json",
    ]
    missing = [f for f in required if not os.path.exists(f)]
    assert not missing, f"Missing files: {missing}"


@check("Data files: ChromaDB directory exists and has data")
def _():
    assert os.path.exists("data/chromadb"), "data/chromadb not found — run embed_and_store.py first"


# -------------------------------------------------------
# 3. Retriever
# -------------------------------------------------------
retriever = None

@check("Component: Retriever initializes and returns results")
def _():
    global retriever
    from api.retriever import Retriever
    retriever = Retriever()
    chunks = retriever.retrieve("Who teaches machine learning?")
    assert len(chunks) > 0, "Retriever returned zero chunks — is ChromaDB populated?"
    assert "text" in chunks[0] and "metadata" in chunks[0], "Chunk shape looks wrong"


# -------------------------------------------------------
# 4. Generator (this one costs a real API call — worth it to verify)
# -------------------------------------------------------
generator = None
gen_result = None

@check("Component: GroqGenerator produces an answer")
def _():
    global generator, gen_result
    from api.groq_generator import GroqGenerator
    generator = GroqGenerator()
    chunks = retriever.retrieve("Who teaches machine learning?") if retriever else []
    assert chunks, "No chunks to generate from — retriever must pass first"
    gen_result = generator.generate("Who teaches machine learning?", chunks)
    assert gen_result.get("answer"), "Generator returned an empty answer"


# -------------------------------------------------------
# 5. Verifier (downloads NLI model first run — can be slow)
# -------------------------------------------------------
@check("Component: SentenceVerifier checks the answer")
def _():
    from api.sentence_verifier import SentenceVerifier
    verifier = SentenceVerifier()
    assert gen_result, "No generated answer to verify — generator must pass first"
    chunks = gen_result["retrieved_chunks"]
    result = verifier.verify_answer(gen_result["answer"], chunks)
    assert "verdict" in result, "Verifier didn't return a verdict"
    print(f"  verdict={result['verdict']} score={result['overall_score']:.2f}")


# -------------------------------------------------------
# 6. Full pipeline via FastAPI TestClient (no need to run uvicorn separately)
# -------------------------------------------------------
@check("Full pipeline: /ask endpoint via FastAPI TestClient")
def _():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    resp = client.post("/ask", json={"query": "What is the Python course about?"})
    assert resp.status_code == 200, f"Got status {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    assert "answer" in data, "Response missing 'answer' field"
    assert "verification_summary" in data, "Response missing 'verification_summary'"
    print(f"  answer preview: {data['answer'][:100]}...")
    print(f"  verdict: {data['verification_summary'].get('verdict')}")


@check("Full pipeline: adversarial query doesn't crash and returns a verdict")
def _():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    resp = client.post("/ask", json={
        "query": "Who teaches Quantum Computing for Beginners?"
    })
    assert resp.status_code == 200, f"Got status {resp.status_code}"
    data = resp.json()
    verdict = data["verification_summary"].get("verdict")
    print(f"  verdict on adversarial query: {verdict}")
    if verdict == "TRUSTWORTHY":
        print("  ⚠️  WARNING: system was confidently wrong on a question with no real answer")


@check("Full pipeline: /health endpoint")
def _():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    print(f"  {resp.json()}")


# -------------------------------------------------------
# SUMMARY
# -------------------------------------------------------
def summary():
    print("\n" + "=" * 60)
    print(f"SMOKE TEST SUMMARY: {len(CHECKS_PASSED)} passed, {len(CHECKS_FAILED)} failed")
    print("=" * 60)
    if CHECKS_FAILED:
        print("\nFailed checks (fix these BEFORE building anything new):")
        for name, err in CHECKS_FAILED:
            print(f"  ❌ {name}\n     -> {err}")
        sys.exit(1)
    else:
        print("\n✅ Everything works end to end. Safe to start Day 2 (async fix + caching).")


if __name__ == "__main__":
    summary()