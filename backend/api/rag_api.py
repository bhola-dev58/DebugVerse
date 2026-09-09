"""
RAG API Endpoints for DebugVerse.
Exposes endpoints for user codebase indexing, semantic search, and vector store metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    from backend.ai.rag_engine import rag_engine
    from backend.ai.codebase_indexer import codebase_indexer
    from backend.auth.supabase_client import get_optional_user
except ImportError:
    from ai.rag_engine import rag_engine
    from ai.codebase_indexer import codebase_indexer
    from auth.supabase_client import get_optional_user

router = APIRouter(prefix="/rag", tags=["RAG & Codebase Indexing"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class FileIndexItem(BaseModel):
    path: str
    content: str


class IndexCodebaseRequest(BaseModel):
    files: List[FileIndexItem]
    session_id: Optional[str] = "default"


class RAGSearchRequest(BaseModel):
    query: str
    language: Optional[str] = "python"
    top_k: Optional[int] = 4
    session_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/index")
async def index_codebase_files(
    req: IndexCodebaseRequest,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    """
    Indexes multiple source code files into the RAG semantic vector store.
    """
    if not req.files:
        raise HTTPException(status_code=400, detail="No files provided for indexing")

    total_chunks = 0
    for f in req.files:
        count = codebase_indexer.index_single_file(
            file_path=f.path,
            content=f.content,
            session_id=req.session_id,
        )
        total_chunks += count

    return {
        "status": "success",
        "message": f"Successfully indexed {len(req.files)} file(s) into {total_chunks} vector chunks.",
        "files_indexed": len(req.files),
        "chunks_indexed": total_chunks,
        "session_id": req.session_id,
    }


@router.post("/search")
async def search_rag(
    req: RAGSearchRequest,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    """
    Performs hybrid semantic vector search over the indexed codebase and documentation.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = rag_engine.retrieve(
        code=req.query,
        language=req.language or "python",
        top_k=req.top_k or 4,
        session_id=req.session_id,
    )

    return {
        "query": req.query,
        "language": req.language,
        "count": len(results),
        "results": results,
    }


@router.get("/stats")
async def get_rag_stats():
    """
    Returns RAG vector database statistics.
    """
    return rag_engine.get_stats()
