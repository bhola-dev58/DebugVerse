"""
Tiered Rate Limiter for DebugVerse.

Limits:
  - anonymous / free  : 10 debug requests per day
  - pro               : 200 debug requests per day (effectively unlimited for normal use)
  - enterprise        : unlimited

Uses Redis for distributed counting across multiple ECS instances.
Falls back to in-memory counting when Redis is unavailable.
"""

import os
import time
import logging
from typing import Dict, Optional, Any
from collections import defaultdict

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Tier limits: (requests_per_day)
TIER_LIMITS: Dict[str, int] = {
    "free": 10,
    "pro": 200,
    "enterprise": 999999,
}

# ── Redis client (lazy init) ───────────────────────────────────────────────────
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()
        logger.info("Redis connected for rate limiting.")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiting ({e}). Using in-memory fallback.")
        return None


# ── In-memory fallback (single instance only) ──────────────────────────────────
_memory_store: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "reset_at": 0})


def _increment_counter(key: str, limit: int) -> tuple[int, int]:
    """
    Increment the request counter for a given key.
    Returns (current_count, seconds_until_reset).
    Uses Redis if available, falls back to in-memory.
    """
    now = int(time.time())
    day_seconds = 86400  # 24 hours
    reset_at = now - (now % day_seconds) + day_seconds  # next midnight UTC

    r = _get_redis()

    if r:
        try:
            pipeline = r.pipeline()
            pipeline.incr(key)
            pipeline.expireat(key, reset_at)
            results = pipeline.execute()
            count = int(results[0])
            ttl = reset_at - now
            return count, ttl
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}. Falling back to memory.")

    # In-memory fallback
    entry = _memory_store[key]
    if now >= entry["reset_at"]:
        entry["count"] = 0
        entry["reset_at"] = reset_at
    entry["count"] += 1
    return entry["count"], reset_at - now


class RateLimiter:
    """Reusable rate limiter that can be applied to any endpoint."""

    def __init__(self, event_type: str = "debug"):
        self.event_type = event_type

    def __call__(self, request: Request) -> None:
        """
        Check rate limit for the current request.
        Reads user info injected by get_current_user dependency.
        """
        # user is injected via request.state by the dependency ordering
        user: Optional[Dict] = getattr(request.state, "current_user", None)

        if user:
            user_id = user.get("sub", "anonymous")
            tier = user.get("tier", "free")
        else:
            user_id = request.client.host if request.client else "unknown"
            tier = "free"

        limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        key = f"ratelimit:{self.event_type}:{user_id}:{_today_key()}"

        count, reset_secs = _increment_counter(key, limit)

        if count > limit:
            reset_minutes = reset_secs // 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "current": count,
                    "tier": tier,
                    "resets_in_minutes": reset_minutes,
                    "upgrade_url": "/pricing",
                    "message": f"Free tier allows {limit} debug requests/day. Upgrade to Pro for unlimited access.",
                },
                headers={"Retry-After": str(reset_secs)},
            )

        # Inject rate limit headers into response (via request.state for middleware pickup)
        request.state.rate_limit_remaining = max(0, limit - count)
        request.state.rate_limit_limit = limit


def _today_key() -> str:
    """Returns YYYY-MM-DD string in UTC for daily bucketing."""
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


# ── Pre-built limiter instances ────────────────────────────────────────────────
debug_rate_limiter = RateLimiter(event_type="debug")
execute_rate_limiter = RateLimiter(event_type="execute")
chat_rate_limiter = RateLimiter(event_type="chat")


async def check_rate_limit(request: Request) -> None:
    """Generic rate limit dependency — used by /debug and /debug/stream."""
    debug_rate_limiter(request)
