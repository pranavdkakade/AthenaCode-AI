import os
from groq import Groq
from typing import List, Dict

_client: Groq | None = None

# Groq model — llama-3.3-70b-versatile (llama3-70b-8192 was decommissioned Apr 2025)
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024
TEMPERATURE = 0.3


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Add it to your .env file: GROQ_API_KEY=your_key"
            )
        _client = Groq(api_key=api_key)
    return _client


def generate_explanation(question: str, chunks: List[Dict]) -> str:
    """
    Sends the retrieved code chunks and user question to the Groq LLM and
    returns a developer-friendly explanation.

    Args:
        question: The natural-language question from the developer.
        chunks: List of relevant code chunk dicts (from retriever).

    Returns:
        LLM-generated explanation string.
    """
    code_context = _format_chunks(chunks)
    messages = [
        {
            "role": "system",
            "content": (
                "You are CodeAtlas AI, an expert software engineering assistant. "
                "You help developers understand codebases by explaining how specific "
                "features and workflows are implemented. "
                "Always cite exact file paths and function names from the provided code. "
                "Use numbered steps when describing multi-step workflows. "
                "Keep explanations clear, concise, and technically accurate."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Developer question: \"{question}\"\n\n"
                f"Relevant code from the repository:\n\n"
                f"{code_context}\n\n"
                f"Based on the code above, explain how this works. "
                f"Reference specific file paths and function names."
            ),
        },
    ]

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    return response.choices[0].message.content.strip()


def _format_chunks(chunks: List[Dict]) -> str:
    """Formats chunk list into a readable multi-block string for the LLM context."""
    sections = []
    for i, chunk in enumerate(chunks, 1):
        sections.append(
            f"[{i}] File: {chunk['file_path']}  |  Function: {chunk['function_name']}  "
            f"|  Language: {chunk.get('language', '?')}\n"
            f"```{chunk.get('language', '')}\n"
            f"{chunk['code']}\n"
            f"```"
        )
    return "\n\n".join(sections)
