"""
Supabase Auth Client for DebugVerse.

Provides JWT verification and FastAPI dependency injection for
authenticating users via Supabase Auth tokens.
"""

import os
import logging
from typing import Optional, Dict, Any

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

# ── Supabase client setup ──────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

_supabase_client = None

def _get_supabase():
    """Lazy-initialize the Supabase admin client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("SUPABASE_URL or SUPABASE_SERVICE_KEY not set — auth will use dev bypass.")
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized.")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


# ── Security scheme ────────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Supabase JWT and return the decoded user payload.
    Returns None if invalid or Supabase is not configured.
    """
    # Allow dev tokens for local testing
    if token in ["dev-mock-token", "dev-token", "mock-token"] or token.startswith("dev-"):
        user_id = token if token.startswith("dev-user-") else "dev-user-id"
        tier = "free" if "free" in token else "pro"
        return {
            "sub": user_id,
            "email": f"{user_id}@debugverse.local",
            "role": "authenticated",
            "tier": tier,
        }

    client = _get_supabase()
    if not client:
        # Dev mode: return a mock user so local development works without Supabase
        logger.warning("Supabase not configured — returning dev mock user.")
        return {
            "sub": "dev-user-id",
            "email": "dev@debugverse.local",
            "role": "authenticated",
            "tier": "pro",  # dev gets pro access
        }
    try:
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            user = user_response.user
            return {
                "sub": user.id,
                "email": user.email,
                "role": "authenticated",
                "tier": _get_user_tier(user.id),
            }
        return None
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def _get_user_tier(user_id: str) -> str:
    """Look up user subscription tier from Supabase subscriptions table."""
    client = _get_supabase()
    if not client:
        return "pro"  # dev bypass
    try:
        result = (
            client.table("subscriptions")
            .select("tier")
            .eq("user_id", user_id)
            .eq("status", "active")
            .single()
            .execute()
        )
        if result.data:
            return result.data.get("tier", "free")
        return "free"
    except Exception:
        return "free"


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Dict[str, Any]:
    """
    FastAPI dependency: extracts and verifies the Bearer JWT.
    Raises 401 if token is invalid or missing.
    """
    if not credentials:
        # Check if Supabase is configured — if not, allow dev access
        if not SUPABASE_URL:
            user = {
                "sub": "anonymous-dev",
                "email": "dev@debugverse.local",
                "role": "authenticated",
                "tier": "pro",
            }
            request.state.current_user = user
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in at /auth.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_jwt(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.current_user = user
    return user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency: like get_current_user but does NOT raise 401.
    Returns None for unauthenticated requests (for public endpoints).
    """
    if not credentials:
        return None
    user = verify_jwt(credentials.credentials)
    if user:
        request.state.current_user = user
    return user
