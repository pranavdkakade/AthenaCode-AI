import os
import json
import pickle
import numpy as np
from typing import List, Dict

# Directory where FAISS indexes and metadata are persisted
# __file__ is ai_pipeline/vector_db/faiss_index.py → go up 2 levels to project root
INDEX_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vector_indexes")

def _load_faiss():
    import faiss

    return faiss


def _index_path(repo_name: str) -> str:
    return os.path.join(INDEX_BASE_DIR, repo_name, "index.faiss")


def _meta_path(repo_name: str) -> str:
    return os.path.join(INDEX_BASE_DIR, repo_name, "metadata.pkl")


def has_index(repo_name: str) -> bool:
    return os.path.exists(_index_path(repo_name)) and os.path.exists(_meta_path(repo_name))


def store_embeddings(chunks: List[Dict], repo_name: str) -> None:
    """
    Builds a FAISS index from chunk embeddings and saves it alongside metadata.

    Args:
        chunks: Chunk dicts with 'embedding' key (numpy float32 array).
        repo_name: Unique identifier for the repository.
    """
    index_dir = os.path.join(INDEX_BASE_DIR, repo_name)
    os.makedirs(index_dir, exist_ok=True)

    vectors = np.stack([c["embedding"] for c in chunks]).astype(np.float32)
    faiss = _load_faiss()
    embedding_dim = vectors.shape[1]

    # Normalise for cosine similarity via inner product search
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(vectors)

    faiss.write_index(index, _index_path(repo_name))

    # Store metadata without embeddings (saves space)
    metadata = [{k: v for k, v in c.items() if k != "embedding"} for c in chunks]
    with open(_meta_path(repo_name), "wb") as f:
        pickle.dump(metadata, f)


def search_embeddings(query_vector: np.ndarray, repo_name: str, top_k: int = 5) -> List[Dict]:
    """
    Searches the FAISS index for the most semantically similar chunks.

    Args:
        query_vector: Embedding of the user's question (shape [768]).
        repo_name: Which repository's index to search.
        top_k: Number of nearest neighbours to return.

    Returns:
        List of chunk metadata dicts ordered by similarity.

    Raises:
        FileNotFoundError: If the repository has not been indexed yet.
    """
    idx_path = _index_path(repo_name)
    meta_path = _meta_path(repo_name)

    if not os.path.exists(idx_path):
        raise FileNotFoundError(
            f"No index found for repository '{repo_name}'. "
            "Please analyze the repository first via POST /api/analyze_repo."
        )

    faiss = _load_faiss()
    index = faiss.read_index(idx_path)

    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    query = query_vector.reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(query)

    scores, indices = index.search(query, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata[idx].copy()
        chunk["similarity_score"] = float(score)
        results.append(chunk)

    return results
