from typing import List, Dict

# Target token range per chunk
MIN_TOKENS = 200
MAX_TOKENS = 500

# Rough characters-per-token estimate for code
CHARS_PER_TOKEN = 4


def chunk_code(parsed_functions: List[Dict], repo_name: str) -> List[Dict]:
    """
    Converts parsed code blocks into indexable chunks with metadata.
    Each function / class becomes its own chunk. Very long functions are split.

    Args:
        parsed_functions: Output from repo_parser.parse_repository().
        repo_name: Name of the repository (used as metadata).

    Returns:
        List of chunk dicts ready for embedding.
    """
    chunks = []
    chunk_id = 0

    for item in parsed_functions:
        code = item["code"]
        sub_chunks = _split_if_too_long(code)

        for idx, sub_code in enumerate(sub_chunks):
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "repo_name": repo_name,
                    "file_path": item["file_path"],
                    "function_name": item["function_name"]
                    + (f"_part{idx + 1}" if len(sub_chunks) > 1 else ""),
                    "language": item.get("language", "unknown"),
                    "code": sub_code,
                    "token_estimate": len(sub_code) // CHARS_PER_TOKEN,
                }
            )
            chunk_id += 1

    return chunks


def _split_if_too_long(code: str) -> List[str]:
    """
    Splits code into segments of roughly MAX_TOKENS if it exceeds the limit.
    Splits on newlines to preserve logical boundaries.
    """
    max_chars = MAX_TOKENS * CHARS_PER_TOKEN

    if len(code) <= max_chars:
        return [code]

    lines = code.splitlines(keepends=True)
    segments = []
    current = []
    current_len = 0

    for line in lines:
        if current_len + len(line) > max_chars and current:
            segments.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        segments.append("".join(current))

    return segments
