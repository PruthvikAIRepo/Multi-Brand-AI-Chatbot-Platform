import secrets
import string
from uuid import UUID
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User, UserBrandAssignment, RefreshToken
from app.models.brand import Brand
from app.models.enums import UserRole
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, AlreadyExistsError, BadRequestError
from app.core.permissions import ALL_BRAND_PERMISSIONS


def _generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password for invited users."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(chars) for _ in range(length))


async def invite_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    role: UserRole,
    brand_ids: list[UUID],
) -> dict:
    """Invite a new admin user. Super Admin only."""
    # Block creating Super Admin via invite
    if role == UserRole.SUPER_ADMIN:
        raise BadRequestError("Cannot invite Super Admin users. Only one Super Admin exists (seed account).")

    # Normalize email to lowercase so it matches login (which lowercases),
    # and so the unique constraint is effectively case-insensitive.
    email = (email or "").strip().lower()

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise AlreadyExistsError("User", "email", email)

    # Deduplicate brand_ids
    brand_ids = list(set(brand_ids))

    # Validate brand_ids exist
    if brand_ids:
        result = await db.execute(
            select(func.count()).select_from(Brand).where(Brand.id.in_(brand_ids))
        )
        count = result.scalar()
        if count != len(brand_ids):
            raise BadRequestError("One or more brand IDs are invalid")

    # Brand assignment is OPTIONAL at creation (SRS §21.4 / UI §23: only email is
    # required). The Super Admin may allot brands now, later, or not at all — an
    # admin with no brands is a valid "pending assignment" state (sees nothing
    # until a brand is assigned). Brands are assigned/changed anytime via
    # update_user_brands.

    # Generate temporary password
    temp_password = _generate_temp_password()

    user = User(
        email=email,
        password_hash=hash_password(temp_password),
        full_name=full_name,
        role=role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    await db.flush()

    # Assign brands with full permissions by default
    for brand_id in brand_ids:
        db.add(UserBrandAssignment(
            user_id=user.id,
            brand_id=brand_id,
            permissions=ALL_BRAND_PERMISSIONS,
        ))

    await db.flush()

    # Send invitation email
    from app.services.email_service import send_invitation_email
    await send_invitation_email(email, full_name, temp_password)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "temp_password": temp_password,
        "assigned_brand_ids": [str(bid) for bid in brand_ids],
    }


async def list_users(db: AsyncSession, page: int = 1, per_page: int = 20) -> tuple[list[dict], int]:
    """List all users with their brand assignments. Paginated."""
    # Count total
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar()

    # Fetch page
    result = await db.execute(
        select(User)
        .options(selectinload(User.brand_assignments).selectinload(UserBrandAssignment.brand))
        .order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = result.scalars().all()

    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "must_change_password": u.must_change_password,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat(),
            "assigned_brands": [
                {
                    "id": str(a.brand_id),
                    "name": a.brand.name,
                    "permissions": a.permissions or [],
                }
                for a in u.brand_assignments
            ],
        }
        for u in users
    ]

    return data, total


async def get_user(db: AsyncSession, user_id: UUID) -> dict:
    """Get a single user with brand assignments and permissions."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.brand_assignments).selectinload(UserBrandAssignment.brand))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat(),
        "assigned_brands": [
            {
                "id": str(a.brand_id),
                "name": a.brand.name,
                "permissions": a.permissions or [],
            }
            for a in user.brand_assignments
        ],
    }


async def update_user_brands(db: AsyncSession, user_id: UUID, brand_ids: list[UUID]) -> dict:
    """Update brand assignments for a user. Super Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    if user.role == UserRole.SUPER_ADMIN:
        raise BadRequestError("Cannot assign brands to Super Admin — they have access to all brands")

    # Deduplicate
    brand_ids = list(set(brand_ids))

    # Empty list is allowed — it un-assigns all brands (parks the admin). The
    # Super Admin controls assignment freely (assign/reassign/remove anytime).
    if brand_ids:
        result = await db.execute(
            select(func.count()).select_from(Brand).where(Brand.id.in_(brand_ids))
        )
        if result.scalar() != len(brand_ids):
            raise BadRequestError("One or more brand IDs are invalid")

    # Remove existing assignments
    result = await db.execute(
        select(UserBrandAssignment).where(UserBrandAssignment.user_id == user_id)
    )
    for assignment in result.scalars().all():
        await db.delete(assignment)

    # Add new assignments with full permissions by default
    for brand_id in brand_ids:
        db.add(UserBrandAssignment(
            user_id=user_id,
            brand_id=brand_id,
            permissions=ALL_BRAND_PERMISSIONS,
        ))

    await db.flush()

    return await get_user(db, user_id)


async def deactivate_user(db: AsyncSession, user_id: UUID, current_user_id: UUID) -> dict:
    """Deactivate a user and revoke all their refresh tokens."""
    if user_id == current_user_id:
        raise BadRequestError("You cannot deactivate your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    was_active = user.is_active
    user.is_active = False

    # Delete all refresh tokens so they can't get new access tokens (delete, not
    # flag-revoked, so a later refresh reads as 'invalid' rather than reuse).
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    await db.flush()

    return {"id": str(user.id), "email": user.email, "is_active": False, "before_is_active": was_active}


async def update_user_permissions(
    db: AsyncSession, user_id: UUID, brand_id: UUID, permissions: list[str]
) -> dict:
    """Update permissions for a user on a specific brand. Super Admin only."""
    # Validate permissions are real
    invalid = [p for p in permissions if p not in ALL_BRAND_PERMISSIONS]
    if invalid:
        raise BadRequestError(f"Invalid permissions: {', '.join(invalid)}")

    result = await db.execute(
        select(UserBrandAssignment).where(
            UserBrandAssignment.user_id == user_id,
            UserBrandAssignment.brand_id == brand_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("User brand assignment")

    assignment.permissions = permissions
    await db.flush()

    return {
        "user_id": str(user_id),
        "brand_id": str(brand_id),
        "permissions": permissions,
    }


async def activate_user(db: AsyncSession, user_id: UUID) -> dict:
    """Reactivate a deactivated user (also clears any lockout)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    was_active = user.is_active
    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()

    return {"id": str(user.id), "email": user.email, "is_active": True, "before_is_active": was_active}


async def unlock_user(db: AsyncSession, user_id: UUID) -> dict:
    """Clear a brute-force lockout (failed attempts + lock) without changing
    the active flag. Super Admin only. Maps to the UI 'Unlock account' action."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    was_locked = bool(user.locked_until) or (user.failed_login_attempts or 0) > 0
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()

    return {"id": str(user.id), "email": user.email, "was_locked": was_locked}
