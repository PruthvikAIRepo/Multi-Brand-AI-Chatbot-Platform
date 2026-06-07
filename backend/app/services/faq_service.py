from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.faq import FAQ
from app.models.embedding import EmbeddingSyncStatus, Embedding
from app.models.enums import EntityType, EmbeddingStatus
from app.core.exceptions import NotFoundError


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def create_faq(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    faq = FAQ(
        brand_id=brand_id,
        question=data["question"],
        answer=data["answer"],
        category=data.get("category"),
    )
    db.add(faq)
    await db.flush()

    db.add(EmbeddingSyncStatus(
        brand_id=brand_id,
        entity_type=EntityType.FAQ,
        entity_id=faq.id,
        status=EmbeddingStatus.PENDING,
    ))
    await db.flush()

    return await _load_faq_response(db, faq.id)


async def list_faqs(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    category: str | None = None,
    search: str | None = None,
    include_deleted: bool = False,
    deleted_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [FAQ.brand_id == brand_id]

    if deleted_only:
        base_filter.append(FAQ.deleted_at.is_not(None))
    elif not include_deleted:
        base_filter.append(FAQ.deleted_at.is_(None))

    if category:
        base_filter.append(FAQ.category == category)
    if search:
        safe = _escape_like(search)
        base_filter.append(FAQ.question.ilike(f"%{safe}%"))

    count_result = await db.execute(
        select(func.count()).select_from(FAQ).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(FAQ)
        .where(*base_filter)
        .order_by(FAQ.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    faqs = result.scalars().all()

    faq_ids = [f.id for f in faqs]
    embed_statuses = await _get_embedding_statuses(db, faq_ids)

    data = [_faq_to_dict(f, embed_statuses.get(f.id)) for f in faqs]
    return data, total


async def get_faq(db: AsyncSession, brand_id: UUID, faq_id: UUID) -> dict:
    result = await db.execute(
        select(FAQ).where(
            FAQ.id == faq_id,
            FAQ.brand_id == brand_id,
            FAQ.deleted_at.is_(None),
        )
    )
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundError("FAQ", str(faq_id))

    embed_statuses = await _get_embedding_statuses(db, [faq.id])
    return _faq_to_dict(faq, embed_statuses.get(faq.id))


async def update_faq(db: AsyncSession, brand_id: UUID, faq_id: UUID, data: dict) -> dict:
    result = await db.execute(
        select(FAQ).where(
            FAQ.id == faq_id,
            FAQ.brand_id == brand_id,
            FAQ.deleted_at.is_(None),
        )
    )
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundError("FAQ", str(faq_id))

    text_changed = False
    for field in ["question", "answer", "category"]:
        if field in data:
            if field in ("question", "answer") and getattr(faq, field) != data[field]:
                text_changed = True
            setattr(faq, field, data[field])

    if text_changed:
        await _update_embedding_status(db, brand_id, faq.id, EmbeddingStatus.PENDING)

    await db.flush()
    return await _load_faq_response(db, faq.id)


async def delete_faq(db: AsyncSession, brand_id: UUID, faq_id: UUID) -> None:
    result = await db.execute(
        select(FAQ).where(
            FAQ.id == faq_id,
            FAQ.brand_id == brand_id,
            FAQ.deleted_at.is_(None),
        )
    )
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundError("FAQ", str(faq_id))

    faq.deleted_at = datetime.now(timezone.utc)

    # Remove embedding sync status
    es_result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.entity_type == EntityType.FAQ,
            EmbeddingSyncStatus.entity_id == faq_id,
        )
    )
    for s in es_result.scalars().all():
        await db.delete(s)

    # Remove vector embeddings
    emb_result = await db.execute(
        select(Embedding).where(
            Embedding.brand_id == brand_id,
            Embedding.entity_type == EntityType.FAQ,
            Embedding.entity_id == faq_id,
        )
    )
    for e in emb_result.scalars().all():
        await db.delete(e)

    await db.flush()


async def restore_faq(db: AsyncSession, brand_id: UUID, faq_id: UUID) -> dict:
    result = await db.execute(
        select(FAQ).where(
            FAQ.id == faq_id,
            FAQ.brand_id == brand_id,
            FAQ.deleted_at.is_not(None),
        )
    )
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundError("Deleted FAQ", str(faq_id))

    faq.deleted_at = None

    db.add(EmbeddingSyncStatus(
        brand_id=brand_id,
        entity_type=EntityType.FAQ,
        entity_id=faq.id,
        status=EmbeddingStatus.PENDING,
    ))
    await db.flush()
    return await _load_faq_response(db, faq.id)


# --- Helpers ---

async def _load_faq_response(db: AsyncSession, faq_id: UUID) -> dict:
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one()
    embed_statuses = await _get_embedding_statuses(db, [faq.id])
    return _faq_to_dict(faq, embed_statuses.get(faq.id))


async def _get_embedding_statuses(db: AsyncSession, faq_ids: list[UUID]) -> dict[UUID, str]:
    if not faq_ids:
        return {}
    result = await db.execute(
        select(EmbeddingSyncStatus.entity_id, EmbeddingSyncStatus.status).where(
            EmbeddingSyncStatus.entity_type == EntityType.FAQ,
            EmbeddingSyncStatus.entity_id.in_(faq_ids),
        )
    )
    return {row.entity_id: row.status.value for row in result.all()}


async def _update_embedding_status(
    db: AsyncSession, brand_id: UUID, faq_id: UUID, status: EmbeddingStatus
) -> None:
    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.entity_type == EntityType.FAQ,
            EmbeddingSyncStatus.entity_id == faq_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = status
        existing.error_message = None
    else:
        db.add(EmbeddingSyncStatus(
            brand_id=brand_id,
            entity_type=EntityType.FAQ,
            entity_id=faq_id,
            status=status,
        ))


def _faq_to_dict(faq: FAQ, embedding_status: str | None = None) -> dict:
    return {
        "id": str(faq.id),
        "brand_id": str(faq.brand_id),
        "question": faq.question,
        "answer": faq.answer,
        "category": faq.category,
        "embedding_status": embedding_status,
        "is_deleted": faq.deleted_at is not None,
        "created_at": faq.created_at.isoformat(),
        "updated_at": faq.updated_at.isoformat(),
    }
