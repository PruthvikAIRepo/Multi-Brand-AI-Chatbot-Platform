from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.routine import Routine, RoutineStep
from app.models.product import Product
from app.models.embedding import EmbeddingSyncStatus, Embedding
from app.models.enums import EntityType, EmbeddingStatus, SkinType
from app.core.exceptions import NotFoundError, BadRequestError


async def create_routine(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    routine = Routine(
        brand_id=brand_id,
        name=data["name"],
        description=data.get("description"),
        target_skin_type=data.get("target_skin_type"),
        target_concerns=data.get("target_concerns", []),
    )
    db.add(routine)
    await db.flush()

    # Add steps
    for step_data in data.get("steps", []):
        # Validate product belongs to same brand
        await _validate_product_brand(db, step_data["product_id"], brand_id)
        db.add(RoutineStep(
            routine_id=routine.id,
            step_number=step_data["step_number"],
            step_name=step_data["step_name"],
            product_id=step_data["product_id"],
            instructions=step_data.get("instructions"),
        ))

    db.add(EmbeddingSyncStatus(
        brand_id=brand_id,
        entity_type=EntityType.ROUTINE,
        entity_id=routine.id,
        status=EmbeddingStatus.PENDING,
    ))

    await db.flush()
    return await _load_routine_response(db, routine.id)


async def list_routines(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    skin_type: SkinType | None = None,
    active_only: bool = True,
    include_deleted: bool = False,
    deleted_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [Routine.brand_id == brand_id]

    if deleted_only:
        base_filter.append(Routine.deleted_at.is_not(None))
    elif not include_deleted:
        base_filter.append(Routine.deleted_at.is_(None))
    if active_only and not include_deleted:
        base_filter.append(Routine.is_active == True)
    if skin_type:
        base_filter.append(Routine.target_skin_type == skin_type)

    count_result = await db.execute(
        select(func.count()).select_from(Routine).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Routine)
        .options(selectinload(Routine.steps).selectinload(RoutineStep.product))
        .where(*base_filter)
        .order_by(Routine.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    routines = result.scalars().unique().all()

    data = [_routine_to_dict(r) for r in routines]
    return data, total


async def get_routine(db: AsyncSession, brand_id: UUID, routine_id: UUID) -> dict:
    result = await db.execute(
        select(Routine)
        .options(selectinload(Routine.steps).selectinload(RoutineStep.product))
        .where(
            Routine.id == routine_id,
            Routine.brand_id == brand_id,
            Routine.deleted_at.is_(None),
        )
    )
    routine = result.scalar_one_or_none()
    if not routine:
        raise NotFoundError("Routine", str(routine_id))

    return _routine_to_dict(routine)


async def update_routine(db: AsyncSession, brand_id: UUID, routine_id: UUID, data: dict) -> dict:
    result = await db.execute(
        select(Routine)
        .options(selectinload(Routine.steps))
        .where(
            Routine.id == routine_id,
            Routine.brand_id == brand_id,
            Routine.deleted_at.is_(None),
        )
    )
    routine = result.scalar_one_or_none()
    if not routine:
        raise NotFoundError("Routine", str(routine_id))

    text_changed = False
    for field in ["name", "description", "target_skin_type", "target_concerns", "is_active"]:
        if field in data:
            if field in ("name", "description") and getattr(routine, field) != data[field]:
                text_changed = True
            setattr(routine, field, data[field])

    # Replace steps if provided
    if "steps" in data:
        for step in routine.steps:
            await db.delete(step)
        for step_data in data["steps"]:
            await _validate_product_brand(db, step_data["product_id"], brand_id)
            db.add(RoutineStep(
                routine_id=routine.id,
                step_number=step_data["step_number"],
                step_name=step_data["step_name"],
                product_id=step_data["product_id"],
                instructions=step_data.get("instructions"),
            ))
        text_changed = True

    if text_changed:
        await _update_embedding_status(db, brand_id, routine.id, EmbeddingStatus.PENDING)

    await db.flush()
    return await _load_routine_response(db, routine.id)


async def delete_routine(db: AsyncSession, brand_id: UUID, routine_id: UUID) -> None:
    result = await db.execute(
        select(Routine).where(
            Routine.id == routine_id,
            Routine.brand_id == brand_id,
            Routine.deleted_at.is_(None),
        )
    )
    routine = result.scalar_one_or_none()
    if not routine:
        raise NotFoundError("Routine", str(routine_id))

    routine.deleted_at = datetime.now(timezone.utc)

    es_result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.entity_type == EntityType.ROUTINE,
            EmbeddingSyncStatus.entity_id == routine_id,
        )
    )
    for s in es_result.scalars().all():
        await db.delete(s)

    emb_result = await db.execute(
        select(Embedding).where(
            Embedding.brand_id == brand_id,
            Embedding.entity_type == EntityType.ROUTINE,
            Embedding.entity_id == routine_id,
        )
    )
    for e in emb_result.scalars().all():
        await db.delete(e)

    await db.flush()


async def restore_routine(db: AsyncSession, brand_id: UUID, routine_id: UUID) -> dict:
    result = await db.execute(
        select(Routine)
        .options(selectinload(Routine.steps).selectinload(RoutineStep.product))
        .where(
            Routine.id == routine_id,
            Routine.brand_id == brand_id,
            Routine.deleted_at.is_not(None),
        )
    )
    routine = result.scalar_one_or_none()
    if not routine:
        raise NotFoundError("Deleted routine", str(routine_id))

    routine.deleted_at = None

    db.add(EmbeddingSyncStatus(
        brand_id=brand_id,
        entity_type=EntityType.ROUTINE,
        entity_id=routine.id,
        status=EmbeddingStatus.PENDING,
    ))
    await db.flush()
    return _routine_to_dict(routine)


# --- Helpers ---

async def _validate_product_brand(db: AsyncSession, product_id: UUID, brand_id: UUID) -> None:
    """Ensure product belongs to the same brand and is not deleted."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
        )
    )
    if not result.scalar_one_or_none():
        raise BadRequestError(f"Product {product_id} not found in this brand or is deleted")


async def _load_routine_response(db: AsyncSession, routine_id: UUID) -> dict:
    result = await db.execute(
        select(Routine)
        .options(selectinload(Routine.steps).selectinload(RoutineStep.product))
        .where(Routine.id == routine_id)
    )
    return _routine_to_dict(result.scalar_one())


async def _update_embedding_status(
    db: AsyncSession, brand_id: UUID, routine_id: UUID, status: EmbeddingStatus
) -> None:
    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.brand_id == brand_id,
            EmbeddingSyncStatus.entity_type == EntityType.ROUTINE,
            EmbeddingSyncStatus.entity_id == routine_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = status
        existing.error_message = None
    else:
        db.add(EmbeddingSyncStatus(
            brand_id=brand_id,
            entity_type=EntityType.ROUTINE,
            entity_id=routine_id,
            status=status,
        ))


def _routine_to_dict(routine: Routine) -> dict:
    return {
        "id": str(routine.id),
        "brand_id": str(routine.brand_id),
        "name": routine.name,
        "description": routine.description,
        "target_skin_type": routine.target_skin_type.value if routine.target_skin_type else None,
        "target_concerns": routine.target_concerns or [],
        "is_active": routine.is_active,
        "is_deleted": routine.deleted_at is not None,
        "step_count": len(routine.steps),
        "steps": [
            {
                "step_number": s.step_number,
                "step_name": s.step_name.value,
                "product_id": str(s.product_id),
                "product_name": s.product.name if s.product else None,
                "product_image_url": s.product.image_url if s.product else None,
                "product_price": str(s.product.price) if s.product else None,
                "instructions": s.instructions,
            }
            for s in sorted(routine.steps, key=lambda x: x.step_number)
        ],
        "created_at": routine.created_at.isoformat(),
        "updated_at": routine.updated_at.isoformat(),
    }
