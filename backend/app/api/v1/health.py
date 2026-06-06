from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import async_session_factory
from app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Check API, database, and Redis connectivity."""
    checks = {"api": "ok", "database": "error", "redis": "error"}

    # Check database — use own session, not the dependency (health check should never fail on commit)
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
    except Exception as e:
        checks["database"] = str(e)

    # Check Redis
    try:
        import redis.asyncio as aioredis

        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "ok"
        await r.aclose()
    except Exception as e:
        checks["redis"] = str(e)

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
    }
