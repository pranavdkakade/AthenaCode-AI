import os
from groq import Groq
from typing import List, Dict

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Set it before starting the backend."
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def explain_code(question: str, chunks: List[Dict]) -> str:
    """
    Given a user question and retrieved code chunks, calls the Groq LLM
    to generate a developer-friendly explanation.

    Args:
        question: The developer's natural-language question.
        chunks: List of chunk dicts containing file_path, function_name, code.

    Returns:
        The LLM-generated explanation as a string.
    """
    code_context = _build_code_context(chunks)
    prompt = _build_prompt(question, code_context)

    client = _get_client()
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are CodeAtlas AI, an expert software engineering assistant. "
                    "Your job is to explain how code works to developers. "
                    "Always reference specific file paths and function names. "
                    "Be concise, accurate, and use numbered steps when describing workflows."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()


def _build_code_context(chunks: List[Dict]) -> str:
    """Formats retrieved chunks into a readable code block for the LLM prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"--- Chunk {i} ---\n"
            f"File: {chunk['file_path']}\n"
            f"Function: {chunk['function_name']}\n"
            f"Language: {chunk.get('language', 'unknown')}\n\n"
            f"{chunk['code']}\n"
        )
    return "\n".join(parts)


def _build_prompt(question: str, code_context: str) -> str:
    return (
        f"A developer asked: \"{question}\"\n\n"
        f"Here are the most relevant code snippets from the repository:\n\n"
        f"{code_context}\n\n"
        f"Using the code snippets above, explain how the answer to the developer's question "
        f"is implemented. Reference specific file paths and function names. "
        f"Use numbered steps if explaining a workflow."
    )
