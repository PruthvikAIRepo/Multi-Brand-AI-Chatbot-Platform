"""Redis-based rate limiter. Per-IP and per-user sliding window.
Uses a shared connection pool — no new connection per call."""

import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

# Shared Redis connection pool (created once, reused)
_redis_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
    return _redis_pool


async def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> dict:
    """Check if a key has exceeded the rate limit within the window."""
    r = _get_redis()
    redis_key = f"rate_limit:{key}"

    current = await r.incr(redis_key)
    if current == 1:
        await r.expire(redis_key, window_seconds)

    ttl = await r.ttl(redis_key)

    return {
        "allowed": current <= limit,
        "remaining": max(limit - current, 0),
        "reset_in": max(ttl, 0),
    }


async def check_chat_rate_limit(
    ip_address: str | None,
    session_id: str | None,
    per_ip_limit: int | None = None,
    per_user_limit: int | None = None,
) -> dict | None:
    """Check both IP and user rate limits. Returns None if allowed."""
    ip_limit = per_ip_limit or settings.RATE_LIMIT_PER_IP
    user_limit = per_user_limit or 30

    if ip_address:
        ip_check = await check_rate_limit(f"ip:{ip_address}", ip_limit)
        if not ip_check["allowed"]:
            return {"message": f"Rate limit exceeded. Try again in {ip_check['reset_in']} seconds.", "reset_in": ip_check["reset_in"]}

    if session_id:
        user_check = await check_rate_limit(f"session:{session_id}", user_limit)
        if not user_check["allowed"]:
            return {"message": f"Too many messages. Try again in {user_check['reset_in']} seconds.", "reset_in": user_check["reset_in"]}

    return None
