from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.routine import RoutineCreateRequest, RoutineUpdateRequest
from app.services import routine_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import SkinType

router = APIRouter(prefix="/brands/{brand_id}/routines", tags=["Routines"])


@router.post("", response_model=dict)
async def create_routine(
    brand_id: UUID,
    request: RoutineCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a routine with steps. Validates products belong to same brand. Requires routines.edit."""
    await check_brand_permission(db, current_user, brand_id, "routines.edit")
    routine = await routine_service.create_routine(db, brand_id, request.model_dump())
    return api_response(data=routine, message="Routine created successfully")


@router.get("", response_model=dict)
async def list_routines(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    skin_type: SkinType | None = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List routines with filters. Requires routines.view."""
    await check_brand_permission(db, current_user, brand_id, "routines.view")
    routines, total = await routine_service.list_routines(
        db, brand_id, page, per_page, skin_type, active_only
    )
    return paginated_response(data=routines, total=total, page=page, per_page=per_page)


@router.get("/deleted", response_model=dict)
async def list_deleted_routines(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List soft-deleted routines. Requires routines.edit."""
    await check_brand_permission(db, current_user, brand_id, "routines.edit")
    routines, total = await routine_service.list_routines(
        db, brand_id, page, per_page, active_only=False, deleted_only=True
    )
    return paginated_response(data=routines, total=total, page=page, per_page=per_page)


@router.get("/{routine_id}", response_model=dict)
async def get_routine(
    brand_id: UUID,
    routine_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a routine with all steps and product details. Requires routines.view."""
    await check_brand_permission(db, current_user, brand_id, "routines.view")
    routine = await routine_service.get_routine(db, brand_id, routine_id)
    return api_response(data=routine)


@router.put("/{routine_id}", response_model=dict)
async def update_routine(
    brand_id: UUID,
    routine_id: UUID,
    request: RoutineUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a routine. Replaces steps if provided. Requires routines.edit."""
    await check_brand_permission(db, current_user, brand_id, "routines.edit")
    routine = await routine_service.update_routine(
        db, brand_id, routine_id, request.model_dump(exclude_unset=True)
    )
    return api_response(data=routine, message="Routine updated successfully")


@router.delete("/{routine_id}", response_model=dict)
async def delete_routine(
    brand_id: UUID,
    routine_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a routine. Requires routines.edit."""
    await check_brand_permission(db, current_user, brand_id, "routines.edit")
    await routine_service.delete_routine(db, brand_id, routine_id)
    return api_response(message="Routine deleted successfully")


@router.post("/{routine_id}/restore", response_model=dict)
async def restore_routine(
    brand_id: UUID,
    routine_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted routine. Requires routines.edit."""
    await check_brand_permission(db, current_user, brand_id, "routines.edit")
    routine = await routine_service.restore_routine(db, brand_id, routine_id)
    return api_response(data=routine, message="Routine restored successfully")
