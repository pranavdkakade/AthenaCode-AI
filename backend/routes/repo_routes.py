from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.repo_cloner import clone_repository, extract_repo_name
from backend.services.repo_parser import parse_repository
from ai_pipeline.chunking.code_chunker import chunk_code

router = APIRouter()


class RepoRequest(BaseModel):
    repo_url: str


class RepoResponse(BaseModel):
    status: str
    repo_name: str
    total_chunks: int
    message: str


@router.post("/analyze_repo", response_model=RepoResponse)
async def analyze_repo(request: RepoRequest):
    """
    Clones the repository, parses all source files, chunks the code,
    generates embeddings, and stores them in the FAISS vector database.
    """
    repo_url = request.repo_url.strip()

    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="Only public GitHub URLs are supported (https://github.com/...).",
        )

    try:
        repo_name = extract_repo_name(repo_url)

        from ai_pipeline.vector_db.faiss_index import has_index

        if has_index(repo_name):
            return RepoResponse(
                status="success",
                repo_name=repo_name,
                total_chunks=0,
                message=f"Repository '{repo_name}' is already indexed.",
            )

        # Step 1: Clone
        repo_path, repo_name = clone_repository(repo_url)

        # Step 2: Parse
        parsed_functions = parse_repository(repo_path)
        if not parsed_functions:
            raise HTTPException(status_code=422, detail="No parseable source files found.")

        # Step 3: Chunk
        chunks = chunk_code(parsed_functions, repo_name)

        # Step 4: Embed
        from ai_pipeline.embeddings.embedder import generate_embeddings

        embedded_chunks = generate_embeddings(chunks)

        # Step 5: Index
        from ai_pipeline.vector_db.faiss_index import store_embeddings

        store_embeddings(embedded_chunks, repo_name)

        return RepoResponse(
            status="success",
            repo_name=repo_name,
            total_chunks=len(chunks),
            message=f"Repository '{repo_name}' analyzed and indexed successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")
