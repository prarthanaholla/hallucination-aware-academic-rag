# ================================================================
# backend/groq_generator.py
# Replaces answer_generator.py — uses Groq instead of Anthropic
#
# Groq is free, runs Llama 3 / Mixtral at ~500 tokens/sec
# Get key at: https://console.groq.com
# ================================================================

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# llama-3.3-70b-versatile was removed from Groq's catalog (confirmed via
# GET /openai/v1/models — no longer listed for this key as of 2026-08-11).
# openai/gpt-oss-120b is the current largest general-purpose chat model
# available on the account; swap here if Groq's lineup changes again.
MODEL     = "openai/gpt-oss-120b"
MAX_TOKENS = 1024

SYSTEM_PROMPT = """You are a precise academic assistant for PES University's 
Computer Science and Engineering department.

Your job:
- Answer student questions about courses, faculty, and academic calendar
- Use ONLY the provided context to answer
- Be factual, concise, and direct
- If information is not in the context, say "I don't have that information in my knowledge base"
- Never make up credits, dates, names, or course details
- Write in clear sentences (this helps with verification)"""


def build_prompt(query: str, context: str) -> str:
    return f"""Context from PESU CSE knowledge base:

{context}

---
Student question: {query}

Answer using only the above context. Be direct and factual:"""


class GroqGenerator:

    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set.\n"
                "Get a free key at https://console.groq.com\n"
                "Then add to .env:  GROQ_API_KEY=gsk_..."
            )
        self.client = Groq(api_key=GROQ_API_KEY)
        print(f"  Groq ready — model: {MODEL}")

    def format_context(self, chunks: list) -> str:
        lines = []
        for i, chunk in enumerate(chunks, 1):
            meta   = chunk["metadata"]
            source = meta.get("source", "")
            ctype  = meta.get("chunk_type", "")
            score  = chunk.get("score", 0)
            lines.append(
                f"[{i}] [{source}/{ctype}] (relevance: {score:.2f})\n{chunk['text']}"
            )
        return "\n\n".join(lines)

    def generate(self, query: str, chunks: list) -> dict:
        context = self.format_context(chunks)
        prompt  = build_prompt(query, context)

        response = self.client.chat.completions.create(
            model      = MODEL,
            max_tokens = MAX_TOKENS,
            temperature= 0,            # 0 = as deterministic as Groq allows,
                                        # needed so eval_harness.py verdicts
                                        # are reproducible run-to-run
            seed       = 42,           # Groq supports a seed hint on top of
                                        # temperature=0 for extra reproducibility;
                                        # harmless if a given model ignores it
            messages   = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ]
        )

        answer = response.choices[0].message.content.strip()

        return {
            "query":              query,
            "answer":             answer,
            "retrieved_chunks":   chunks,
            "context":            context,
            "model":              MODEL,
            "temperature":        0,
            "seed":               42,
            "prompt_tokens":      response.usage.prompt_tokens,
            "completion_tokens":  response.usage.completion_tokens,
        }


# ── Quick test ───────────────────────────────────────────────────
if __name__ == "__main__":
    gen = GroqGenerator()

    dummy_chunks = [{
        "text": ("Python For Computational Problem Solving (UE25CS151A) "
                 "is a Foundation Course in Semester 1. Credits: Total=5. "
                 "Tools: Python interpreter 3.8+, IDLE, Jupyter."),
        "metadata": {"source": "courses", "chunk_type": "overview",
                     "course_code": "UE25CS151A"},
        "score": 0.94
    }]

    result = gen.generate(
        "What is the Python course and how many credits?",
        dummy_chunks
    )

    print(f"Answer: {result['answer']}")
    print(f"Tokens: {result['prompt_tokens']} prompt / {result['completion_tokens']} completion")