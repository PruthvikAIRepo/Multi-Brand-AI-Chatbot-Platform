"""Celery tasks for async embedding generation.
Products/FAQs/routines are embedded asynchronously — admin CRUD never waits for embedding."""

import asyncio
from uuid import UUID
from app.tasks.celery_app import celery_app
from app.db.session import async_session_factory
from app.services import embedding_service
from app.models.embedding import EmbeddingSyncStatus
from app.models.enums import EmbeddingStatus, EntityType
from sqlalchemy import select


@celery_app.task(name="app.tasks.embedding_tasks.embed_entity")
def embed_entity_task(brand_id: str, entity_type: str, entity_id: str):
    """Celery task: generate embedding for a single entity."""
    asyncio.run(_embed_entity(UUID(brand_id), EntityType(entity_type), UUID(entity_id)))


async def _embed_entity(brand_id: UUID, entity_type: EntityType, entity_id: UUID):
    async with async_session_factory() as db:
        try:
            await embedding_service.embed_entity(db, brand_id, entity_type, entity_id)
            await db.commit()
        except Exception:
            await db.rollback()


@celery_app.task(name="app.tasks.embedding_tasks.embed_all_pending")
def embed_all_pending_task(brand_id: str):
    """Celery task: embed all pending items for a brand."""
    asyncio.run(_embed_all_pending(UUID(brand_id)))


async def _embed_all_pending(brand_id: UUID):
    async with async_session_factory() as db:
        result = await db.execute(
            select(EmbeddingSyncStatus).where(
                EmbeddingSyncStatus.brand_id == brand_id,
                EmbeddingSyncStatus.status == EmbeddingStatus.PENDING,
            )
        )
        pending = result.scalars().all()

        for item in pending:
            try:
                await embedding_service.embed_entity(db, brand_id, item.entity_type, item.entity_id)
            except Exception:
                pass  # Individual failures don't block others

        await db.commit()
