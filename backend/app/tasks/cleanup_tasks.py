"""Celery tasks for data cleanup and retention.
SRS Section 16.1: Conversations older than retention period are auto-purged."""

import asyncio
from datetime import datetime, timedelta, timezone
from app.tasks.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.brand_config import BrandConfig
from app.models.conversation import Conversation
from app.models.user import RefreshToken, PasswordResetToken
from sqlalchemy import select, delete


@celery_app.task(name="app.tasks.cleanup_tasks.purge_expired_conversations")
def purge_expired_conversations():
    """Delete conversations older than the brand's retention period.
    Runs daily via Celery Beat."""
    asyncio.run(_purge_conversations())


async def _purge_conversations():
    async with async_session_factory() as db:
        # Get all brand configs with retention settings
        result = await db.execute(select(BrandConfig))
        configs = result.scalars().all()

        total_purged = 0
        for config in configs:
            days = config.conversation_retention_days or 90
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Delete old conversations (CASCADE deletes messages)
            del_result = await db.execute(
                delete(Conversation).where(
                    Conversation.brand_id == config.brand_id,
                    Conversation.started_at < cutoff,
                )
            )
            total_purged += del_result.rowcount

        await db.commit()
        return {"purged_conversations": total_purged}


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Delete expired refresh tokens and used password reset tokens.
    Runs hourly via Celery Beat."""
    asyncio.run(_cleanup_tokens())


async def _cleanup_tokens():
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)

        # Delete expired refresh tokens
        await db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now)
        )

        # Delete used password reset tokens
        await db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.used == True)
        )

        # Delete expired password reset tokens
        await db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
        )

        await db.commit()
