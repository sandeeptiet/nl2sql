import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.database import SessionLocal
from app.models.db_models import FewShotExample
from app.models.schemas import RetrieverOutput, Example
from typing import List

# load once at module level
embedder = SentenceTransformer("all-MiniLM-L6-v2")

_index    : faiss.IndexFlatL2 = faiss.IndexFlatL2(384)
_examples : List[FewShotExample] = []

def build_faiss_index():
    """Build FAISS index from few_shot_examples table. Called at startup."""
    global _index, _examples

    db = SessionLocal()
    try:
        _examples = db.query(FewShotExample).all()
        if not _examples:
            print("  No examples found — FAISS index empty.")
            _index = faiss.IndexFlatL2(384)
            return

        questions   = [e.question for e in _examples]
        embeddings  = embedder.encode(questions, convert_to_numpy=True)
        embeddings  = embeddings.astype("float32")

        _index = faiss.IndexFlatL2(embeddings.shape[1])
        _index.add(embeddings)  # type: ignore[call-arg]
        print(f"  FAISS index built with {len(_examples)} examples.")
    finally:
        db.close()

def retrieve_examples(question: str, k: int = 3) -> RetrieverOutput:
    """Return top-k similar Q→SQL examples for the given question."""
    if _index is None or _index.ntotal == 0:
        return RetrieverOutput(examples=[])

    query_vec = embedder.encode([question], convert_to_numpy=True)
    query_vec = query_vec.astype("float32")

    k_actual = min(k, _index.ntotal)
    _, indices = _index.search(query_vec, k_actual)  # type: ignore[call-arg]

    examples = []
    for idx in indices[0]:
        if idx < len(_examples):
            ex = _examples[idx]
            examples.append(Example(
                question=str(ex.question),
                sql=str(ex.sql),
                query_type=str(ex.query_type) if ex.query_type else None,
            ))

    return RetrieverOutput(examples=examples)
