from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import InviteUserRequest, UpdateUserBrandsRequest, UpdateUserPermissionsRequest
from app.services import user_service
from app.core.permissions import require_super_admin
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/users", tags=["User Management"])


@router.post("", response_model=dict)
async def invite_user(
    request: InviteUserRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new admin user. Super Admin only."""
    result = await user_service.invite_user(
        db, request.email, request.full_name, request.role, request.brand_ids
    )
    return api_response(data=result, message="User invited successfully")


@router.get("", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all admin users with pagination. Super Admin only."""
    users, total = await user_service.list_users(db, page, per_page)
    return paginated_response(data=users, total=total, page=page, per_page=per_page)


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single user's details. Super Admin only."""
    user = await user_service.get_user(db, user_id)
    return api_response(data=user)


@router.put("/{user_id}/brands", response_model=dict)
async def update_user_brands(
    user_id: UUID,
    request: UpdateUserBrandsRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update brand assignments for a user. Super Admin only."""
    user = await user_service.update_user_brands(db, user_id, request.brand_ids)
    return api_response(data=user, message="Brand assignments updated")


@router.put("/{user_id}/brands/{brand_id}/permissions", response_model=dict)
async def update_user_permissions(
    user_id: UUID,
    brand_id: UUID,
    request: UpdateUserPermissionsRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update permissions for a user on a specific brand. Super Admin only."""
    result = await user_service.update_user_permissions(db, user_id, brand_id, request.permissions)
    return api_response(data=result, message="Permissions updated")


@router.get("/permissions/all", response_model=dict)
async def list_all_permissions(
    current_user: User = Depends(require_super_admin),
):
    """List all available permissions. Useful for the UI to show checkboxes."""
    from app.core.permissions import ALL_BRAND_PERMISSIONS
    return api_response(data=ALL_BRAND_PERMISSIONS)


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user and revoke all their tokens. Super Admin only."""
    result = await user_service.deactivate_user(db, user_id, current_user.id)
    return api_response(data=result, message="User deactivated")


@router.post("/{user_id}/activate", response_model=dict)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a deactivated user. Super Admin only."""
    result = await user_service.activate_user(db, user_id)
    return api_response(data=result, message="User activated")
