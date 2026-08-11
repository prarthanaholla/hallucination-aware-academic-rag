# ================================================================
# debug_verification.py
#
# Shows the EXACT generated answer, the exact evidence chunk used,
# and the raw NLI scores (entailment/contradiction/neutral) for a
# specific query — so we can see precisely why the verifier scored
# it the way it did, instead of guessing.
#
# Run from Backend/ root:
#   python -m tests.debug_verification
# ================================================================

from api.retriever import Retriever
from api.groq_generator import GroqGenerator
from api.sentence_verifier import SentenceVerifier

QUERIES_TO_DEBUG = [
    "When is the FAM 2 (Faculty Advisor Meeting 2) for even semesters?",
]


def main():
    retriever = Retriever()
    generator = GroqGenerator()
    verifier  = SentenceVerifier()

    for query in QUERIES_TO_DEBUG:
        print(f"\n{'='*70}")
        print(f"QUERY: {query}")
        print(f"{'='*70}")

        chunks = retriever.retrieve(query)
        gen_result = generator.generate(query, chunks)

        print(f"\nEXACT GENERATED ANSWER:")
        print(f'  "{gen_result["answer"]}"')

        print(f"\nRETRIEVED CHUNKS (what the verifier can check against):")
        for i, c in enumerate(chunks, 1):
            print(f"  [{i}] source={c['metadata'].get('source')} "
                  f"score={c['score']:.3f}")
            print(f"      {c['text'][:200]}")

        # Now split into verification units the same way the real
        # pipeline does, and show the RAW nli_scores per unit
        units = verifier.split_sentences(gen_result["answer"])
        print(f"\nSPLIT INTO {len(units)} VERIFICATION UNIT(S):")
        for i, unit in enumerate(units, 1):
            print(f'  [{i}] "{unit}"')

        print(f"\nRAW NLI SCORES PER UNIT (this is the real evidence):")
        for i, unit in enumerate(units, 1):
            result = verifier.verify_sentence(unit, chunks)
            print(f"\n  Unit [{i}]: \"{unit}\"")
            print(f"    label: {result['label']}")
            print(f"    confidence: {result['confidence']}")
            print(f"    raw nli_scores: {result['nli_scores']}")
            print(f"    best matching evidence chunk (first 200 chars):")
            print(f"      {result['evidence'][:200]}")


if __name__ == "__main__":
    main()