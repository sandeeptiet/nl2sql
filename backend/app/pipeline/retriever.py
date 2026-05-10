import math
from collections import Counter
from app.core.database import SessionLocal
from app.models.db_models import FewShotExample
from app.models.schemas import RetrieverOutput, Example
from typing import List

# Pure-Python BM25 — no numpy, no native extensions, works everywhere.
class _BM25:
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        n = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / n if n else 1
        df: dict[str, int] = {}
        for doc in corpus:
            for word in set(doc):
                df[word] = df.get(word, 0) + 1
        self.idf = {
            w: math.log((n - f + 0.5) / (f + 0.5) + 1)
            for w, f in df.items()
        }

    def get_scores(self, query: list[str]) -> list[float]:
        scores = []
        for doc in self.corpus:
            dl = len(doc)
            freq = Counter(doc)
            score = 0.0
            for w in query:
                if w not in self.idf:
                    continue
                tf = freq.get(w, 0)
                score += self.idf[w] * tf * (self.k1 + 1) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                )
            scores.append(score)
        return scores


_bm25     : _BM25 | None = None
_examples : List[FewShotExample] = []


def build_faiss_index():
    """Build BM25 index from few_shot_examples table. Called at startup."""
    global _bm25, _examples

    db = SessionLocal()
    try:
        _examples = db.query(FewShotExample).all()
        if not _examples:
            print("  No examples found — BM25 index empty.")
            return

        tokenized = [e.question.lower().split() for e in _examples]
        _bm25 = _BM25(tokenized)
        print(f"  BM25 index built with {len(_examples)} examples.")
    finally:
        db.close()


def retrieve_examples(question: str, k: int = 3) -> RetrieverOutput:
    """Return top-k similar Q→SQL examples for the given question."""
    if _bm25 is None or not _examples:
        return RetrieverOutput(examples=[])

    scores = _bm25.get_scores(question.lower().split())
    top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]

    return RetrieverOutput(examples=[
        Example(
            question=str(_examples[i].question),
            sql=str(_examples[i].sql),
            query_type=str(_examples[i].query_type) if _examples[i].query_type else None,
        )
        for i in top_indices
    ])
