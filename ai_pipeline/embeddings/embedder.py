import os
import numpy as np
from typing import List, Dict

# A lighter sentence-transformers model is much faster for local indexing.
MODEL_NAME = os.environ.get(
    "CODEATLAS_EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
BATCH_SIZE = int(os.environ.get("CODEATLAS_EMBED_BATCH_SIZE", "32"))

_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)


def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    """
    Generates embeddings for code chunks in batches.

    Args:
        chunks: List of chunk dicts from code_chunker.

    Returns:
        Same list with an added 'embedding' key.
    """
    _load_model()

    texts = [f"{chunk['function_name']}\n{chunk['code']}" for chunk in chunks]
    vectors = _model.encode(
        texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)

    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector

    return chunks


def embed_query(question: str) -> np.ndarray:
    """
    Embeds a natural-language question.

    Args:
        question: Developer's plain-text question.

    Returns:
        Embedding as a numpy float32 array.
    """
    _load_model()
    vector = _model.encode(
        question,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vector.astype(np.float32)
