from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.user import User, UserBrandAssignment
from app.models.enums import UserRole
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

security_scheme = HTTPBearer()

# All possible brand-level permissions
# Super Admin bypasses all of these — has implicit full access
# Admin users get a subset assigned per brand
ALL_BRAND_PERMISSIONS = [
    # Brand management
    "brand.view",
    "brand.edit",
    "brand.config.edit",

    # Content management
    "products.view",
    "products.edit",
    "faqs.view",
    "faqs.edit",
    "routines.view",
    "routines.edit",

    # Rules & compliance
    "compliance.view",
    "compliance.edit",
    "recommendations.view",
    "recommendations.edit",

    # Tone & styling
    "tone.view",
    "tone.edit",
    "image_styles.view",
    "image_styles.edit",

    # Prompt management
    "prompt.view",
    "prompt.edit",

    # Conversations & analytics
    "conversations.view",
    "analytics.view",

    # Leads
    "leads.view",
    "leads.export",
    "leads.delete",

    # Moderation
    "moderation.view",
    "moderation.edit",

    # Channels
    "channels.view",
    "channels.edit",

    # Embedding & logs
    "embedding.view",
    "logs.view",

    # Emergency
    "emergency.override",
]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate user from JWT token. Used on every protected route."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise UnauthorizedError()

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError()

    result = await db.execute(
        select(User)
        .options(selectinload(User.brand_assignments))
        .where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or deactivated")

    return user


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Only Super Admin can access this route."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Super Admin access required")
    return current_user


async def require_brand_access(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify the user has access to the specified brand.
    Super Admin has access to all brands.
    Admin must have the brand in their assignments."""
    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user

    assigned_brand_ids = {a.brand_id for a in current_user.brand_assignments}
    if brand_id not in assigned_brand_ids:
        raise ForbiddenError("You do not have access to this brand")

    return current_user


async def check_brand_permission(
    db: AsyncSession,
    current_user: User,
    brand_id: UUID,
    permission: str,
) -> None:
    """Check if the user has a specific permission on a brand.
    Super Admin always passes.
    Admin must have the permission in their brand assignment."""
    if current_user.role == UserRole.SUPER_ADMIN:
        return  # Super Admin has all permissions

    # Find the assignment for this user + brand
    result = await db.execute(
        select(UserBrandAssignment).where(
            UserBrandAssignment.user_id == current_user.id,
            UserBrandAssignment.brand_id == brand_id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ForbiddenError("You do not have access to this brand")

    # Check permission
    user_permissions = assignment.permissions or []
    if permission not in user_permissions:
        raise ForbiddenError(f"You do not have '{permission}' permission for this brand")


def get_user_brand_ids(user: User) -> list[UUID] | None:
    """Get list of brand IDs the user can access.
    Returns None for Super Admin (means all brands).
    Returns list of UUIDs for Admin."""
    if user.role == UserRole.SUPER_ADMIN:
        return None
    return [a.brand_id for a in user.brand_assignments]
