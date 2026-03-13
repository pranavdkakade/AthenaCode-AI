import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure project root is importable when running from backend/ (e.g. uvicorn main:app)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()  # load .env before anything else
from backend.routes.repo_routes import router as repo_router
from backend.routes.query_routes import router as query_router

app = FastAPI(
    title="CodeAtlas AI",
    description="LLM-Powered GitHub Codebase Mapping and Documentation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your extension's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repo_router, prefix="/api", tags=["Repository"])
app.include_router(query_router, prefix="/api", tags=["Query"])


@app.get("/")
async def root():
    return {"message": "CodeAtlas AI backend is running.", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
