"""Admin endpoint to trigger embedding generation for a brand's content."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.embedding import EmbeddingSyncStatus
from app.models.enums import EmbeddingStatus
from app.services import embedding_service, audit_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response
from app.models.user import User
from app.models.enums import AdminActionType

router = APIRouter(prefix="/brands/{brand_id}/embed", tags=["Embedding Generation"])


@router.post("/all", response_model=dict)
async def embed_all_pending(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate embeddings for all pending items in a brand. Requires embedding.view."""
    await check_brand_permission(db, current_user, brand_id, "embedding.view")

    # Get all pending items
    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.status == EmbeddingStatus.PENDING,
        )
    )
    pending = result.scalars().all()

    success = 0
    failed = 0
    errors = []

    for item in pending:
        try:
            await embedding_service.embed_entity(db, brand_id, item.entity_type, item.entity_id)
            success += 1
        except Exception as e:
            failed += 1
            errors.append({"entity_id": str(item.entity_id), "error": str(e)})

    await db.flush()

    await audit_service.log_action(
        db, current_user.id, AdminActionType.CREATED, "embedding_batch",
        brand_id=brand_id, entity_name=f"{success} embedded, {failed} failed",
    )
    return api_response(data={
        "total_pending": len(pending),
        "success": success,
        "failed": failed,
        "errors": errors[:5],  # Show first 5 errors only
    }, message=f"Embedded {success} items, {failed} failed")
