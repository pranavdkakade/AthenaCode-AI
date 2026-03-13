from typing import List, Dict


def retrieve_chunks(search_results: List[Dict]) -> List[Dict]:
    """
    Post-processes raw FAISS search results to produce clean, de-duplicated
    chunk records ready for the LLM prompt.

    Args:
        search_results: Output from faiss_index.search_embeddings().

    Returns:
        Filtered and ranked list of chunk dicts.
    """
    seen_functions = set()
    cleaned = []

    for chunk in search_results:
        # De-duplicate by (file_path, function_name)
        key = (chunk.get("file_path", ""), chunk.get("function_name", ""))
        if key in seen_functions:
            continue
        seen_functions.add(key)

        cleaned.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "repo_name": chunk.get("repo_name", ""),
                "file_path": chunk.get("file_path", ""),
                "function_name": chunk.get("function_name", ""),
                "language": chunk.get("language", "unknown"),
                "code": chunk.get("code", ""),
                "similarity_score": chunk.get("similarity_score", 0.0),
            }
        )

    # Sort by similarity descending (highest relevance first)
    cleaned.sort(key=lambda x: x["similarity_score"], reverse=True)

    return cleaned
