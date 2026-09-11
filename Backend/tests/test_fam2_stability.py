# ================================================================
# test_fam2_stability.py
#
# Reruns the FAM 2 query several times end-to-end and checks
# whether the verdict is now stable after:
#   1. NLI model upgrade (small -> base)
#   2. Groq temperature=0 + seed=42
#
# Run from Backend/ so the relative imports below resolve:
#   python test_fam2_stability.py
#
# Adjust the three import lines below if your module paths differ
# from PROJECT_CONTEXT.md's layout.
# ================================================================

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from api.retriever import Retriever            # adjust path/name if different
from api.groq_generator import GroqGenerator
from api.sentence_verifier import SentenceVerifier

QUERY = "When is the FAM 2 (Faculty Advisor Meeting 2) for even semesters?"
N_RUNS = 8

def main():
    retriever = Retriever()
    generator = GroqGenerator()
    verifier  = SentenceVerifier()

    chunks = retriever.retrieve(QUERY)   # adjust method name if different

    verdicts = []
    print(f"Running '{QUERY}' {N_RUNS} times...\n")

    for i in range(1, N_RUNS + 1):
        gen_result = generator.generate(QUERY, chunks)
        answer = gen_result["answer"]

        verify_result = verifier.verify_answer(answer, chunks)
        verdict = verify_result["verdict"]
        verdicts.append(verdict)

        print(f"[Run {i}] verdict={verdict}  answer={answer[:80]!r}")

    print("\n--- Summary ---")
    unique = set(verdicts)
    print(f"Verdicts seen: {verdicts}")
    if len(unique) == 1:
        print(f"STABLE — every run produced '{unique.pop()}'.")
    else:
        print(f"STILL UNSTABLE — {len(unique)} distinct verdicts across {N_RUNS} runs: {unique}")
        print("If still unstable, the overlap-rescue threshold (0.85) may still")
        print("need loosening, or the NLI model may need to go to '-large'.")

if __name__ == "__main__":
    main()