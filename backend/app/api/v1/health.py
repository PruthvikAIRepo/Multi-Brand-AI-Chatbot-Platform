from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import async_session_factory
from app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Check API, database, and Redis connectivity."""
    settings = get_settings()
    is_dev = settings.ENVIRONMENT == "development"
    checks = {"api": "ok", "database": "error", "redis": "error"}

    # Check database
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
    except Exception as e:
        checks["database"] = str(e) if is_dev else "error"

    # Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "ok"
        await r.aclose()
    except Exception as e:
        checks["redis"] = str(e) if is_dev else "error"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
    }
