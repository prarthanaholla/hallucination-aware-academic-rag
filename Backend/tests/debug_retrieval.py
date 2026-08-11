# ================================================================
# debug_retrieval.py
#
# Prints exactly what got retrieved for a specific query, and why
# (top_k used, filters applied, each chunk's source/type/score).
#
# Run from Backend/ root:
#   python -m tests.debug_retrieval
# ================================================================

from api.retriever import Retriever

QUERIES_TO_DEBUG = [
    "List the electives available in 6th semester",   # the one that failed
    "List the electives of 6th semester",              # the original phrasing that worked before
]


def main():
    r = Retriever()

    for query in QUERIES_TO_DEBUG:
        top_k = r._detect_top_k(query)
        filters = r._detect_filters(query)
        chunks = r.retrieve(query)

        print(f"\n{'='*70}")
        print(f"QUERY: {query}")
        print(f"top_k used: {top_k}")
        print(f"filters used: {filters}")
        print(f"chunks returned: {len(chunks)}")
        print(f"{'-'*70}")

        sources_seen = {}
        for i, c in enumerate(chunks, 1):
            src = c["metadata"].get("source")
            ctype = c["metadata"].get("chunk_type")
            sources_seen[src] = sources_seen.get(src, 0) + 1
            print(f"  [{i}] score={c['score']:.3f} source={src:10s} "
                  f"type={ctype:20s} | {c['text'][:70]}...")

        print(f"{'-'*70}")
        print(f"Source breakdown: {sources_seen}")


if __name__ == "__main__":
    main()