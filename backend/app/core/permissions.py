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


def get_user_brand_ids(user: User) -> list[UUID] | None:
    """Get list of brand IDs the user can access.
    Returns None for Super Admin (means all brands).
    Returns list of UUIDs for Admin."""
    if user.role == UserRole.SUPER_ADMIN:
        return None  # None = all brands
    return [a.brand_id for a in user.brand_assignments]
