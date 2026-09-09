"""
Debug Session History API for DebugVerse.

Provides persistent session storage in Supabase with dev-mode in-memory fallback.
Users can retrieve, paginate, and delete their debug history from any device.
"""

import uuid
import datetime
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])

# Import auth dependency
try:
    from backend.auth.supabase_client import get_current_user
except ImportError:
    from auth.supabase_client import get_current_user

# In-memory dev/test fallback session store
_dev_sessions: List[Dict[str, Any]] = []


class SaveSessionRequest(BaseModel):
    language: str
    code: str
    ai_response: Optional[str] = None
    raw_markdown: Optional[str] = None
    model_used: Optional[str] = None
    rag_citations: Optional[List[Dict[str, Any]]] = []
    routing_info: Optional[Dict[str, Any]] = {}
    execution_output: Optional[str] = None


def _get_supabase_client():
    """Get the Supabase service-role client."""
    try:
        from backend.auth.supabase_client import _get_supabase
        return _get_supabase()
    except Exception:
        try:
            from auth.supabase_client import _get_supabase
            return _get_supabase()
        except Exception:
            return None


@router.get("", response_model=List[Dict[str, Any]])
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    language: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user),
):
    """
    Retrieve paginated debug session history for the authenticated user.
    """
    user_id = current_user["sub"]
    client = _get_supabase_client()

    # If dev token or client unavailable, serve from memory
    if user_id == "dev-user-id" or not client:
        res = [s for s in _dev_sessions if (not language or s.get("language") == language)]
        return res[offset : offset + limit]

    try:
        query = (
            client.table("debug_sessions")
            .select("id,language,code,ai_response,model_used,rag_citations,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if language:
            query = query.eq("language", language)

        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Supabase history fetch fallback: {e}")
        return _dev_sessions[offset : offset + limit]


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_session(
    session: SaveSessionRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Save a debug session to persistent storage."""
    user_id = current_user["sub"]
    client = _get_supabase_client()
    session_id = str(uuid.uuid4())

    new_record = {
        "id": session_id,
        "user_id": user_id,
        "language": session.language,
        "code": session.code,
        "ai_response": session.ai_response or "",
        "raw_markdown": session.raw_markdown or "",
        "model_used": session.model_used or "gemini-2.5-flash",
        "rag_citations": session.rag_citations or [],
        "routing_info": session.routing_info or {},
        "execution_output": session.execution_output,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    _dev_sessions.insert(0, new_record)

    if user_id == "dev-user-id" or not client:
        return {"id": session_id, "status": "saved"}

    try:
        result = client.table("debug_sessions").insert(new_record).execute()
        return {"id": result.data[0]["id"] if result.data else session_id, "status": "saved"}
    except Exception as e:
        logger.warning(f"Supabase history insert fallback: {e}")
        return {"id": session_id, "status": "saved"}


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
):
    """Delete a specific debug session by ID."""
    global _dev_sessions
    _dev_sessions = [s for s in _dev_sessions if s.get("id") != session_id]

    user_id = current_user["sub"]
    client = _get_supabase_client()
    if not client or user_id == "dev-user-id":
        return

    try:
        client.table("debug_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
    except Exception as e:
        logger.warning(f"Supabase history delete fallback: {e}")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_history(
    current_user: Dict = Depends(get_current_user),
):
    """Delete ALL debug sessions for the authenticated user."""
    _dev_sessions.clear()

    user_id = current_user["sub"]
    client = _get_supabase_client()
    if not client or user_id == "dev-user-id":
        return

    try:
        client.table("debug_sessions").delete().eq("user_id", user_id).execute()
    except Exception as e:
        logger.warning(f"Supabase clear history fallback: {e}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_usage_stats(
    current_user: Dict = Depends(get_current_user),
):
    """Return usage statistics for the current user's dashboard."""
    user_id = current_user["sub"]
    client = _get_supabase_client()

    if user_id == "dev-user-id" or not client:
        return {
            "total_sessions": len(_dev_sessions),
            "today_debugs": len(_dev_sessions),
            "this_month_debugs": len(_dev_sessions),
            "tier": current_user.get("tier", "pro"),
            "languages": ["python", "javascript"],
        }

    try:
        today = datetime.datetime.now(datetime.UTC).date().isoformat()
        month_start = datetime.datetime.now(datetime.UTC).replace(day=1).date().isoformat()

        total_result = client.table("debug_sessions").select("id", count="exact").eq("user_id", user_id).execute()
        today_result = (
            client.table("usage_events")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("event_type", "debug")
            .gte("created_at", f"{today}T00:00:00Z")
            .execute()
        )
        month_result = (
            client.table("usage_events")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("event_type", "debug")
            .gte("created_at", f"{month_start}T00:00:00Z")
            .execute()
        )

        return {
            "total_sessions": total_result.count or len(_dev_sessions),
            "today_debugs": today_result.count or 0,
            "this_month_debugs": month_result.count or 0,
            "tier": current_user.get("tier", "free"),
            "languages": ["python", "javascript"],
        }
    except Exception as e:
        logger.warning(f"Supabase stats query fallback: {e}")
        return {
            "total_sessions": len(_dev_sessions),
            "today_debugs": 0,
            "this_month_debugs": 0,
            "tier": current_user.get("tier", "free"),
            "languages": ["python"],
        }
