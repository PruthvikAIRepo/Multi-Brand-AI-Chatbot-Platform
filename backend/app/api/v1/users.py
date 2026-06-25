from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import InviteUserRequest, UpdateUserBrandsRequest, UpdateUserPermissionsRequest
from app.services import user_service, audit_service, auth_service
from app.core.permissions import require_super_admin
from app.core.request_utils import get_client_ip
from app.config import get_settings
from app.models.enums import AdminActionType
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/users", tags=["User Management"])


@router.post("", response_model=dict)
async def invite_user(
    request: InviteUserRequest,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new admin user and assign brand(s). Super Admin only."""
    result = await user_service.invite_user(
        db, request.email, request.full_name, request.role, request.brand_ids
    )
    await audit_service.log_action(
        db, current_user.id, AdminActionType.INVITED, "user",
        entity_id=UUID(result["id"]), entity_name=result["email"],
        ip_address=get_client_ip(http_request),
        after_state={"role": result["role"], "brands": result["assigned_brand_ids"]},
    )
    # Never echo the temp password in production — it is delivered by email.
    # In development we return it so local testing works without SMTP.
    if get_settings().ENVIRONMENT != "development":
        result.pop("temp_password", None)
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


# Fixed: /permissions/all BEFORE /{user_id} to prevent route conflict
@router.get("/permissions/all", response_model=dict)
async def list_all_permissions(
    current_user: User = Depends(require_super_admin),
):
    """List all available permissions. Useful for the UI to show checkboxes."""
    from app.core.permissions import ALL_BRAND_PERMISSIONS
    return api_response(data=ALL_BRAND_PERMISSIONS)


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
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update brand assignments for a user. Super Admin only."""
    before = await user_service.get_user(db, user_id)
    before_ids = [b["id"] for b in before["assigned_brands"]]
    user = await user_service.update_user_brands(db, user_id, request.brand_ids)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "user_brands",
        entity_id=user_id, ip_address=get_client_ip(http_request),
        before_state={"brand_ids": before_ids},
        after_state={"brand_ids": [str(b) for b in request.brand_ids]},
    )
    return api_response(data=user, message="Brand assignments updated")


@router.put("/{user_id}/brands/{brand_id}/permissions", response_model=dict)
async def update_user_permissions(
    user_id: UUID,
    brand_id: UUID,
    request: UpdateUserPermissionsRequest,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update permissions for a user on a specific brand. Super Admin only."""
    before = await user_service.get_user(db, user_id)
    before_perms = next(
        (b["permissions"] for b in before["assigned_brands"] if b["id"] == str(brand_id)), []
    )
    result = await user_service.update_user_permissions(db, user_id, brand_id, request.permissions)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "user_permissions",
        entity_id=user_id, brand_id=brand_id, ip_address=get_client_ip(http_request),
        before_state={"permissions": before_perms},
        after_state={"permissions": request.permissions},
    )
    return api_response(data=result, message="Permissions updated")


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: UUID,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user (revoke access) and revoke all their tokens. Super Admin only."""
    result = await user_service.deactivate_user(db, user_id, current_user.id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.DISABLED, "user",
        entity_id=user_id, ip_address=get_client_ip(http_request),
        before_state={"is_active": result["before_is_active"]},
        after_state={"is_active": False},
    )
    return api_response(data=result, message="User deactivated")


@router.post("/{user_id}/activate", response_model=dict)
async def activate_user(
    user_id: UUID,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a deactivated user. Super Admin only."""
    result = await user_service.activate_user(db, user_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.ENABLED, "user",
        entity_id=user_id, ip_address=get_client_ip(http_request),
        before_state={"is_active": result["before_is_active"]},
        after_state={"is_active": True},
    )
    return api_response(data=result, message="User activated")


@router.post("/{user_id}/unlock", response_model=dict)
async def unlock_user(
    user_id: UUID,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Clear a brute-force lockout on a user account. Super Admin only."""
    result = await user_service.unlock_user(db, user_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "user_unlock",
        entity_id=user_id, ip_address=get_client_ip(http_request),
        after_state={"was_locked": result["was_locked"], "unlocked": True},
    )
    return api_response(data=result, message="Account unlocked")


@router.post("/{user_id}/reset-password", response_model=dict)
async def admin_reset_password(
    user_id: UUID,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Send a password-reset email to a user (Super Admin only).

    Reuses the standard reset flow: it emails a single-use, time-limited token to
    the user's address and never sets or reveals a password to the Super Admin.
    Useful for helping a locked-out admin or resending onboarding. No-op (still 200)
    if the account is inactive or absent, to avoid leaking which accounts exist."""
    user = await user_service.get_user(db, user_id)  # 404 if the id is invalid
    await auth_service.forgot_password(db, user["email"])
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "user_password_reset",
        entity_id=user_id, entity_name=user["email"],
        ip_address=get_client_ip(http_request),
    )
    return api_response(message="Password reset email sent if the account is active")
