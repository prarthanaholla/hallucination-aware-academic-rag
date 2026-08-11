# ================================================================
# backend/sentence_verifier.py  (v2)
# ================================================================

import re
import re as _re  
import nltk
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

nltk.download("punkt",     quiet=True)
nltk.download("punkt_tab", quiet=True)

NLI_MODEL          = "cross-encoder/nli-deberta-v3-small"
VERIFIED_THRESHOLD = 0.7
PARTIAL_THRESHOLD  = 0.4
VERIFIED           = "VERIFIED"
PARTIAL            = "PARTIAL"
HALLUCINATED       = "HALLUCINATED"
ABSTAINED          = "ABSTAINED"

REFUSAL_PATTERNS = [
    r"don'?t have (that|this|the) information",
    r"not (available|found) in (my|the) knowledge base",
    r"i don'?t know",
    r"cannot find (that|this|any) information",
    r"no information (is )?available",
    r"unable to (find|answer|provide)",
]

def is_refusal(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in REFUSAL_PATTERNS)

# ── List detection ────────────────────────────────────────────────
# Answers that are numbered lists should be verified as ONE unit
LIST_PATTERNS = [
    r"^\s*\d+\.\s+\S",           # starts with "1. something"
    r":\s*\n?\s*\d+\.\s+\S",     # "... are: 1. something"
    r"\s+\d+\.\s+[A-Z]",         # inline "... 1. Name 2. Name"
    r":\s*[-•]\s+\S",            # bullet list
]

def is_list_answer(text: str) -> bool:
    """Detect if the answer is a numbered/bulleted list."""
    for p in LIST_PATTERNS:
        if re.search(p, text):
            return True
    return False


def collapse_list_answer(text: str) -> list[str]:
    """
    For list answers, return as a SINGLE verification unit
    instead of splitting into fragments.
    This prevents name fragments like 'Dr. Vaishali Shinde 2.'
    from being verified in isolation.
    """
    return [text.strip()]


class SentenceVerifier:

    def __init__(self):
        print("Loading NLI model (first run downloads ~180MB)...")
        self.tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
        self.model     = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL)
        self.model.eval()
        self.label_map = {0: "contradiction", 1: "entailment", 2: "neutral"}
        print("  NLI model ready\n")

    def split_into_clauses(self, sentence: str) -> list[str]:
        """
        Break a compound sentence into smaller single-fact clauses.

        Why: small NLI models get less confident checking a whole
        sentence when it combines multiple distinct facts (e.g. name +
        designation + email in one sentence), even when each fact is
        individually correct. Splitting at natural joints (', and' /
        '; ') lets each fact get verified on its own.
        """
        parts = re.split(r",?\s+and\s+|;\s+", sentence)
        parts = [p.strip() for p in parts if len(p.strip()) > 5]
        return parts if len(parts) > 1 else [sentence]

    def split_sentences(self, text: str) -> list[str]:
        """
        Smart sentence splitting:
        - List answers → kept as ONE unit (prevents fragment verification)
        - Normal prose → split by sentence, then each sentence is
          further split into single-fact clauses where possible
        """
        if is_list_answer(text):
            return collapse_list_answer(text)

        sentences = nltk.sent_tokenize(text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        clauses = []
        for s in sentences:
            clauses.extend(self.split_into_clauses(s))
        return clauses

    def nli_score(self, premise: str, hypothesis: str) -> dict:
        # Truncate very long premises to fit model context
        inputs = self.tokenizer(
            premise[:1000],      # cap premise length
            hypothesis,
            return_tensors = "pt",
            truncation     = True,
            max_length     = 512,
            padding        = True,
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0].tolist()
        return {
            "contradiction": round(probs[0], 4),
            "entailment":    round(probs[1], 4),
            "neutral":       round(probs[2], 4),
        }

    def verify_sentence(self, sentence: str, chunks: list) -> dict:
        # --- Refusal detection: don't fact-check an honest "I don't know" ---
        if is_refusal(sentence):
            return {
                "sentence": sentence, "label": ABSTAINED, "confidence": 1.0,
                "evidence": "", "source": {},
                "nli_scores": {"note": "honest refusal detected, NLI skipped"},
            }

        # --- Exact-match short-circuit for verifiable facts (unchanged) ---
        email_matches = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', sentence)
        for email in email_matches:
            for chunk in chunks:
                if email.lower() in chunk["text"].lower():
                    return {
                        "sentence": sentence, "label": VERIFIED, "confidence": 1.0,
                        "evidence": chunk["text"][:300], "source": chunk["metadata"],
                        "nli_scores": {"note": "exact-match short-circuit, NLI skipped"},
                    }

        # --- NLI scoring (unchanged) ---
        best_entailment = 0.0
        best_chunk      = None
        best_scores     = None

        for chunk in chunks:
            scores = self.nli_score(chunk["text"], sentence)
            if scores["entailment"] > best_entailment:
                best_entailment = scores["entailment"]
                best_chunk      = chunk
                best_scores     = scores

        # --- NEW: lexical overlap rescue ---
        # If NLI is unsure (not VERIFIED) but NOT contradicting, AND
        # the hypothesis is near-verbatim to the premise, trust the
        # surface match over NLI's unreliable probability.
        if best_chunk and best_entailment < VERIFIED_THRESHOLD:
            overlap = self.lexical_overlap(sentence, best_chunk["text"])
            contradiction = best_scores["contradiction"] if best_scores else 1.0
            if overlap >= 0.85 and contradiction < 0.15:
                return {
                    "sentence": sentence, "label": VERIFIED,
                    "confidence": round(overlap, 4),
                    "evidence": best_chunk["text"][:300],
                    "source": best_chunk["metadata"],
                    "nli_scores": {
                        **(best_scores or {}),
                        "note": f"lexical-overlap rescue ({overlap:.2f}), NLI was unreliable"
                    },
                }

        # --- Fall back to standard NLI-based labeling (unchanged) ---
        if best_entailment >= VERIFIED_THRESHOLD:
            label, confidence = VERIFIED, best_entailment
        elif best_entailment >= PARTIAL_THRESHOLD:
            label, confidence = PARTIAL, best_entailment
        else:
            label, confidence = HALLUCINATED, 1.0 - best_entailment

        return {
            "sentence": sentence, "label": label, "confidence": round(confidence, 4),
            "evidence": best_chunk["text"][:300] if best_chunk else "",
            "source": best_chunk["metadata"] if best_chunk else {},
            "nli_scores": best_scores,
        }

    def verify_answer(self, answer: str, chunks: list) -> dict:
        sentences = self.split_sentences(answer)
        results   = []

        is_list = is_list_answer(answer)
        print(f"  Answer type: {'LIST (single unit)' if is_list else 'PROSE'}")
        print(f"  Verifying {len(sentences)} unit(s)...")

        for i, sentence in enumerate(sentences):
            result = self.verify_sentence(sentence, chunks)
            results.append(result)
            print(f"    [{i+1}] {result['label']} ({result['confidence']:.2f})")

        verified     = sum(1 for r in results if r["label"] == VERIFIED)
        partial      = sum(1 for r in results if r["label"] == PARTIAL)
        hallucinated = sum(1 for r in results if r["label"] == HALLUCINATED)
        abstained    = sum(1 for r in results if r["label"] == ABSTAINED)
        total        = len(results)

        # Abstentions are excluded from the faithfulness score — an
        # honest refusal is neither a verified fact nor a hallucination
        scoreable = verified + partial + hallucinated
        overall_score = (verified * 1.0 + partial * 0.5) / scoreable if scoreable > 0 else (1.0 if abstained > 0 else 0)

        # A partial abstention (some units "I don't know", others actual
        # claims) can't earn full TRUSTWORTHY — the answer is admittedly
        # incomplete even if the claims it did make check out.
        partially_abstained = 0 < abstained < total

        if abstained == total and total > 0:
            verdict = "ABSTAINED"
        elif overall_score >= 0.8:
            verdict = "MIXED" if partially_abstained else "TRUSTWORTHY"
        elif overall_score >= 0.5:
            verdict = "MIXED"
        else:
            verdict = "UNRELIABLE"

        return {
            "sentences":            results,
            "overall_score":        round(overall_score, 4),
            "verified_count":       verified,
            "partial_count":        partial,
            "hallucinated_count":   hallucinated,
            "abstained_count":      abstained,
            "total_sentences":      total,
            "verdict":              verdict,
            "answer_type":          "list" if is_list else "prose",
        }
    STOPWORDS = {"a", "an", "the", "is", "in", "at", "of", "and", "to",
                 "their", "her", "his", "for", "on", "with", "this"}

    def lexical_overlap(self, hypothesis: str, premise: str) -> float:
        """
        What fraction of the hypothesis's meaningful words also appear
        in the premise. High overlap = strong surface-level evidence
        of support, independent of NLI's (sometimes unreliable) opinion.
        """
        def clean_words(text):
            words = re.findall(r"[a-zA-Z0-9@.]+", text.lower())
            return set(w for w in words if w not in self.STOPWORDS and len(w) > 1)

        h_words = clean_words(hypothesis)
        p_words = clean_words(premise)
        if not h_words:
            return 0.0
        return len(h_words & p_words) / len(h_words)