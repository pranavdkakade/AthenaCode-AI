from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_pipeline.rag.retriever import retrieve_chunks
from typing import List
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    repo_name: str
    top_k: int = 5


class FileReference(BaseModel):
    file_path: str
    function_name: str
    language: str
    snippet: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    references: List[FileReference]


@router.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """
    Converts the user question into an embedding, performs semantic search
    over the indexed repository, and returns an LLM-generated explanation
    with file references.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not request.repo_name.strip():
        raise HTTPException(status_code=400, detail="repo_name cannot be empty.")

    try:
        # Embed the question
        from ai_pipeline.embeddings.embedder import embed_query

        query_vector = embed_query(request.question)

        # Search FAISS index
        from ai_pipeline.vector_db.faiss_index import search_embeddings

        raw_results = search_embeddings(query_vector, request.repo_name, top_k=request.top_k)
        if not raw_results:
            return QueryResponse(
                question=request.question,
                answer="No relevant code found. Make sure the repository has been analyzed first.",
                references=[],
            )

        # Retrieve full chunk metadata
        chunks = retrieve_chunks(raw_results)

        # Generate explanation via Groq LLM
        from ai_pipeline.rag.generator import generate_explanation

        answer = generate_explanation(request.question, chunks)

        references = [
            FileReference(
                file_path=c["file_path"],
                function_name=c["function_name"],
                language=c["language"],
                snippet=c["code"][:300],
            )
            for c in chunks
        ]

        return QueryResponse(
            question=request.question,
            answer=answer,
            references=references,
        )

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Query error:\n%s", tb)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}\n\n{tb}")
