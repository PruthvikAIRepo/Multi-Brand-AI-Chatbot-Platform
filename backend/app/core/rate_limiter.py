"""Redis-based rate limiter. Per-IP and per-user sliding window."""

import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> dict:
    """Check if a key has exceeded the rate limit within the window.
    Returns {allowed: bool, remaining: int, reset_in: int}."""

    r = aioredis.from_url(settings.REDIS_URL)

    try:
        redis_key = f"rate_limit:{key}"

        # Increment counter
        current = await r.incr(redis_key)

        # Set expiry only on first request in window
        if current == 1:
            await r.expire(redis_key, window_seconds)

        ttl = await r.ttl(redis_key)

        if current > limit:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in": max(ttl, 0),
            }

        return {
            "allowed": True,
            "remaining": limit - current,
            "reset_in": max(ttl, 0),
        }
    finally:
        await r.aclose()


async def check_chat_rate_limit(
    ip_address: str | None,
    session_id: str | None,
    per_ip_limit: int | None = None,
    per_user_limit: int | None = None,
) -> dict | None:
    """Check both IP and user rate limits for chat endpoint.
    Returns None if allowed, or {message, reset_in} if blocked."""

    ip_limit = per_ip_limit or settings.RATE_LIMIT_PER_IP
    user_limit = per_user_limit or 30  # Default per-user

    # Check per-IP
    if ip_address:
        ip_check = await check_rate_limit(f"ip:{ip_address}", ip_limit)
        if not ip_check["allowed"]:
            return {
                "message": f"Rate limit exceeded. Try again in {ip_check['reset_in']} seconds.",
                "reset_in": ip_check["reset_in"],
            }

    # Check per-session (user)
    if session_id:
        user_check = await check_rate_limit(f"session:{session_id}", user_limit)
        if not user_check["allowed"]:
            return {
                "message": f"Too many messages. Try again in {user_check['reset_in']} seconds.",
                "reset_in": user_check["reset_in"],
            }

    return None  # Allowed
