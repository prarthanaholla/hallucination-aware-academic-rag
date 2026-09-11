# ================================================================
# eval_harness.py
#
# Runs a fixed test set of questions through the existing pipeline
# (Retriever -> GroqGenerator -> SentenceVerifier) and reports
# REAL, aggregate numbers instead of eyeballing single answers.
#
# This is what turns "I built a hallucination-aware RAG system"
# into "I measured it: 82% verified, 91% retrieval hit-rate."
#
# Usage:
#   python eval_harness.py
#
# Output:
#   - Printed summary table (console)
#   - eval_results.json  (full per-question results, for the README
#     or for digging into specific failures)
# ================================================================

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import json
import time
from api.retriever import Retriever
from api.groq_generator import GroqGenerator
from api.sentence_verifier import SentenceVerifier

RESULTS_FILE = "eval_results.json"

# -------------------------------------------------------
# TEST SET
#
# Fill in / expand this to 20-30 real questions covering all
# three data sources (courses, faculty, calendar), plus a few
# ADVERSARIAL questions your system SHOULD refuse or flag —
# e.g. asking about a course/faculty member that doesn't exist.
# Those are the most important rows: a good hallucination-aware
# system should score LOW confidence / abstain on these, not
# confidently make something up.
#
# expected_chunk_source: optional — used to check retrieval
# actually pulled from the right place (courses/faculty/calendar)
# expected_keywords: optional — words that SHOULD appear in a
# correct answer, used as a cheap correctness proxy
# is_adversarial: True for questions with NO good answer in the
# knowledge base — success here means the system says so instead
# of hallucinating a confident-sounding wrong answer
# -------------------------------------------------------
TEST_SET = [
    # --- Calendar: verified against oddsem_calender.pdf (Aug-Dec 2025, sems 1/3/5/7)
    # and evensem_calender.pdf (Jan-May 2026, sems 2/4/6/8) ---
    {"query": "When is ISA 1 for odd semesters?", "expected_chunk_source": "calendar",
     "expected_keywords": ["22", "September"], "category": "calendar"},
    {"query": "When is ISA 2 for even semesters?", "expected_chunk_source": "calendar",
     "expected_keywords": ["April", "May"], "category": "calendar"},
    {"query": "What are all the holidays for odd semester 2025?", "expected_chunk_source": "calendar",
     "expected_keywords": ["Independence Day"], "category": "calendar"},
    {"query": "When do classes commence for semesters 1, 3, 5, 7?",
     "expected_chunk_source": "calendar", "expected_keywords": ["4", "August"], "category": "calendar"},
    {"query": "When is the FAM 2 (Faculty Advisor Meeting 2) for even semesters?",
     "expected_chunk_source": "calendar", "expected_keywords": ["April"], "category": "calendar"},
    {"query": "When will results be announced for even semesters (Jan-May 2026 session)?",
     "expected_chunk_source": "calendar", "expected_keywords": ["June"], "category": "calendar"},

    # --- Faculty: verified against faculty.json ---
    {"query": "What is the email of Ankita Singhai?", "expected_chunk_source": "faculty",
     "expected_keywords": ["ankitasinghai@pes.edu"], "category": "faculty"},
    {"query": "What is Dr. Sandesh BJ's designation and email?", "expected_chunk_source": "faculty",
     "expected_keywords": ["Chairperson", "sandesh_bj@pes.edu"], "category": "faculty"},
    {"query": "Which faculty specialize in cyber security?", "expected_chunk_source": "faculty",
     "expected_keywords": ["Gokul", "Geetha", "Vinodha"], "category": "faculty"},
    {"query": "Who works on machine learning at PES CSE?", "expected_chunk_source": "faculty",
     "expected_keywords": [], "category": "faculty"},
    {"query": "What are Dr. Arti Arya's areas of expertise?", "expected_chunk_source": "faculty",
     "expected_keywords": ["Artificial Intelligence", "Natural Language Processing"], "category": "faculty"},

    # --- Courses: verified against courses.json ---
    {"query": "How many credits is the Python for Computational Problem Solving course?",
     "expected_chunk_source": "courses", "expected_keywords": ["5"], "category": "courses"},
    {"query": "What semester is the Python course (UE25CS151A) offered in?",
     "expected_chunk_source": "courses", "expected_keywords": ["1"], "category": "courses"},
    {"query": "What are the course objectives for the Python course?",
     "expected_chunk_source": "courses", "expected_keywords": ["lists", "tuples"], "category": "courses"},
    {"query": "List the electives available in 6th semester",
     "expected_chunk_source": "courses", "expected_keywords": ["Elective"], "category": "courses"},

    # --- Generalization checks: same bug CATEGORIES as the ones we
    # fixed, but different specific facts never used while writing the
    # fixes. If these pass with zero further code changes, that's real
    # evidence the fixes target the mechanism, not the test case. ---
    {"query": "List the electives available in 5th semester",
     "expected_chunk_source": "courses", "expected_keywords": ["Elective"],
     "category": "generalization_retriever_filter"},
    {"query": "What is the email of Dr. Vinodha K?",
     "expected_chunk_source": "faculty", "expected_keywords": ["vinodhak@pes.edu"],
     "category": "generalization_exact_match"},
    {"query": "What is Dr. Richa Sharma's designation and email?",
     "expected_chunk_source": "faculty",
     "expected_keywords": ["Associate Professor", "richasharma@pes.edu"],
     "category": "generalization_clause_split"},

    # --- Adversarial: nothing in the KB should support these — a good
    # hallucination-aware system should abstain / score low, not answer
    # confidently. This is the most important category. ---
    {"query": "Who teaches Quantum Computing for Beginners?",
     "expected_chunk_source": None, "expected_keywords": [],
     "category": "adversarial", "is_adversarial": True},
    {"query": "What is the email of Professor Rajesh Kumar Sharma, Dean of Astrophysics?",
     "expected_chunk_source": None, "expected_keywords": [],
     "category": "adversarial", "is_adversarial": True},
    {"query": "When is ISA 3 scheduled?",
     "expected_chunk_source": None, "expected_keywords": [],
     "category": "adversarial", "is_adversarial": True},
    {"query": "How many credits is the Blockchain Fundamentals course worth?",
     "expected_chunk_source": None, "expected_keywords": [],
     "category": "adversarial", "is_adversarial": True},
    {"query": "What is the email of the faculty member who teaches Astrophysics?",
     "expected_chunk_source": None, "expected_keywords": [],
     "category": "adversarial", "is_adversarial": True},
]


def check_retrieval_hit(chunks, expected_source):
    if not expected_source:
        return None  # not applicable (adversarial / unspecified)
    return any(c["metadata"].get("source") == expected_source for c in chunks)


def check_keyword_hit(answer, expected_keywords):
    if not expected_keywords:
        return None
    answer_lower = answer.lower()
    return any(kw.lower() in answer_lower for kw in expected_keywords)


def run_eval():
    print("=== PESU RAG — Evaluation Harness ===\n")
    retriever = Retriever()
    generator = GroqGenerator()
    verifier  = SentenceVerifier()

    results = []

    for i, case in enumerate(TEST_SET, 1):
        query = case["query"]
        print(f"\n[{i}/{len(TEST_SET)}] {query}")

        t0 = time.time()
        chunks     = retriever.retrieve(query)
        gen_result = generator.generate(query, chunks)
        ver_result = verifier.verify_answer(gen_result["answer"], chunks)
        elapsed = round(time.time() - t0, 2)

        retrieval_hit = check_retrieval_hit(chunks, case.get("expected_chunk_source"))
        keyword_hit   = check_keyword_hit(gen_result["answer"], case.get("expected_keywords"))

        result = {
            "query":            query,
            "category":         case.get("category"),
            "is_adversarial":   case.get("is_adversarial", False),
            "answer":           gen_result["answer"],
            "verdict":          ver_result["verdict"],
            "overall_score":    ver_result["overall_score"],
            "verified_count":   ver_result["verified_count"],
            "partial_count":    ver_result["partial_count"],
            "hallucinated_count": ver_result["hallucinated_count"],
            "retrieval_hit":    retrieval_hit,
            "keyword_hit":      keyword_hit,
            "elapsed_s":        elapsed,
        }
        results.append(result)

        print(f"  verdict={result['verdict']} score={result['overall_score']:.2f} "
              f"retrieval_hit={retrieval_hit} keyword_hit={keyword_hit} ({elapsed}s)")

    print_summary(results)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to {RESULTS_FILE}")


def print_summary(results):
    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)

    normal = [r for r in results if not r["is_adversarial"]]
    adversarial = [r for r in results if r["is_adversarial"]]

    def pct(n, d):
        return round(100 * n / d, 1) if d else 0.0

    # --- Normal questions: do we get the answer right? ---
    if normal:
        avg_score = sum(r["overall_score"] for r in normal) / len(normal)
        trustworthy = sum(1 for r in normal if r["verdict"] == "TRUSTWORTHY")
        retrieval_hits = [r["retrieval_hit"] for r in normal if r["retrieval_hit"] is not None]
        keyword_hits = [r["keyword_hit"] for r in normal if r["keyword_hit"] is not None]

        print(f"\nNormal questions (n={len(normal)}):")
        print(f"  Avg verification score : {avg_score:.2%}")
        print(f"  TRUSTWORTHY verdicts    : {trustworthy}/{len(normal)} "
              f"({pct(trustworthy, len(normal))}%)")
        if retrieval_hits:
            print(f"  Retrieval hit-rate      : {pct(sum(retrieval_hits), len(retrieval_hits))}% "
                  f"(pulled from the correct source)")
        if keyword_hits:
            print(f"  Keyword hit-rate        : {pct(sum(keyword_hits), len(keyword_hits))}% "
                  f"(expected term appeared in answer)")

    # --- Adversarial: does it avoid confidently making things up? ---
    if adversarial:
        # Success = verdict is NOT trustworthy (system correctly flagged low confidence)
        correctly_flagged = sum(1 for r in adversarial if r["verdict"] != "TRUSTWORTHY")
        print(f"\nAdversarial questions (n={len(adversarial)}) — no real answer exists:")
        print(f"  Correctly flagged as unreliable : {correctly_flagged}/{len(adversarial)} "
              f"({pct(correctly_flagged, len(adversarial))}%)")
        for r in adversarial:
            flag = "OK" if r["verdict"] != "TRUSTWORTHY" else "FAILED (hallucinated confidently)"
            print(f"    [{flag}] \"{r['query']}\" -> verdict={r['verdict']} "
                  f"score={r['overall_score']:.2f}")

    print("=" * 65)


if __name__ == "__main__":
    run_eval()