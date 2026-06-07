from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.embedding import EmbeddingSyncStatus
from app.models.enums import EntityType, EmbeddingStatus
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/brands/{brand_id}/embedding-status", tags=["Embedding Status"])


@router.get("", response_model=dict)
async def list_embedding_status(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    entity_type: EntityType | None = None,
    status: EmbeddingStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List embedding sync status. Requires embedding.view."""
    await check_brand_permission(db, current_user, brand_id, "embedding.view")

    filters = [EmbeddingSyncStatus.brand_id == brand_id]
    if entity_type:
        filters.append(EmbeddingSyncStatus.entity_type == entity_type)
    if status:
        filters.append(EmbeddingSyncStatus.status == status)

    count_result = await db.execute(
        select(func.count()).select_from(EmbeddingSyncStatus).where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(EmbeddingSyncStatus)
        .where(*filters)
        .order_by(EmbeddingSyncStatus.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = result.scalars().all()

    data = [
        {
            "id": str(s.id),
            "entity_type": s.entity_type.value if s.entity_type else None,
            "entity_id": str(s.entity_id),
            "status": s.status.value if s.status else None,
            "error_message": s.error_message,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in items
    ]

    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/summary", response_model=dict)
async def embedding_status_summary(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary counts: total, synced, pending, failed. Requires embedding.view."""
    await check_brand_permission(db, current_user, brand_id, "embedding.view")

    result = await db.execute(
        select(EmbeddingSyncStatus.status, func.count(EmbeddingSyncStatus.id))
        .where(EmbeddingSyncStatus.brand_id == brand_id)
        .group_by(EmbeddingSyncStatus.status)
    )
    counts = {row[0].value: row[1] for row in result.all()}

    return api_response(data={
        "total": sum(counts.values()),
        "synced": counts.get("completed", 0),
        "pending": counts.get("pending", 0),
        "failed": counts.get("failed", 0),
    })


@router.post("/{entity_id}/retry", response_model=dict)
async def retry_embedding(
    brand_id: UUID,
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed embedding. Sets status back to pending. Requires embedding.view."""
    await check_brand_permission(db, current_user, brand_id, "embedding.view")

    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.entity_id == entity_id,
        )
    )
    status = result.scalar_one_or_none()
    if not status:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Embedding status", str(entity_id))

    status.status = EmbeddingStatus.PENDING
    status.error_message = None
    await db.flush()

    return api_response(data={
        "entity_id": str(entity_id),
        "status": "pending",
    }, message="Embedding retry queued")
