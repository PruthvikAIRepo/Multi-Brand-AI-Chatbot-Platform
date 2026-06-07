"""Redis caching layer for brand configs.
SRS Section 11.2: Brand configs preloaded, cached to avoid DB hits on every chat message.
Cache invalidated on any config update."""

import json
from uuid import UUID
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

_redis: aioredis.Redis | None = None
CACHE_TTL = 300  # 5 minutes


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, max_connections=10, decode_responses=True)
    return _redis


async def get_cached(key: str) -> dict | None:
    """Get a cached value. Returns None if not cached."""
    r = _get_redis()
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cached(key: str, value: dict, ttl: int = CACHE_TTL) -> None:
    """Cache a value with TTL."""
    r = _get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def invalidate(key: str) -> None:
    """Invalidate a cached key."""
    r = _get_redis()
    await r.delete(key)


async def invalidate_brand(brand_id: UUID) -> None:
    """Invalidate all cached configs for a brand. Called on any config update."""
    r = _get_redis()
    keys = [
        f"brand_config:{brand_id}",
        f"tone_settings:{brand_id}",
        f"moderation_config:{brand_id}",
        f"system_prompt:{brand_id}",
    ]
    for key in keys:
        await r.delete(key)
