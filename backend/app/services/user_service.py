import secrets
import string
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User, UserBrandAssignment
from app.models.brand import Brand
from app.models.enums import UserRole
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, AlreadyExistsError, BadRequestError, ForbiddenError


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
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise AlreadyExistsError("User", "email", email)

    # Validate brand_ids exist
    if brand_ids:
        result = await db.execute(
            select(func.count()).select_from(Brand).where(Brand.id.in_(brand_ids))
        )
        count = result.scalar()
        if count != len(brand_ids):
            raise BadRequestError("One or more brand IDs are invalid")

    # Admin role requires at least one brand assignment
    if role == UserRole.ADMIN and not brand_ids:
        raise BadRequestError("Admin users must be assigned to at least one brand")

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

    # Assign brands
    for brand_id in brand_ids:
        assignment = UserBrandAssignment(user_id=user.id, brand_id=brand_id)
        db.add(assignment)

    await db.flush()

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "temp_password": temp_password,
        "assigned_brand_ids": [str(bid) for bid in brand_ids],
    }


async def list_users(db: AsyncSession) -> list[dict]:
    """List all users with their brand assignments."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.brand_assignments).selectinload(UserBrandAssignment.brand))
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
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
                {"id": str(a.brand_id), "name": a.brand.name}
                for a in u.brand_assignments
            ],
        }
        for u in users
    ]


async def get_user(db: AsyncSession, user_id: UUID) -> dict:
    """Get a single user with brand assignments."""
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
            {"id": str(a.brand_id), "name": a.brand.name}
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

    # Validate brand_ids
    if brand_ids:
        result = await db.execute(
            select(func.count()).select_from(Brand).where(Brand.id.in_(brand_ids))
        )
        if result.scalar() != len(brand_ids):
            raise BadRequestError("One or more brand IDs are invalid")

    if not brand_ids:
        raise BadRequestError("Admin users must be assigned to at least one brand")

    # Remove existing assignments
    result = await db.execute(
        select(UserBrandAssignment).where(UserBrandAssignment.user_id == user_id)
    )
    for assignment in result.scalars().all():
        await db.delete(assignment)

    # Add new assignments
    for brand_id in brand_ids:
        db.add(UserBrandAssignment(user_id=user_id, brand_id=brand_id))

    await db.flush()

    return await get_user(db, user_id)


async def deactivate_user(db: AsyncSession, user_id: UUID, current_user_id: UUID) -> dict:
    """Deactivate a user (revoke access). Super Admin only."""
    if user_id == current_user_id:
        raise BadRequestError("You cannot deactivate your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    user.is_active = False
    await db.flush()

    return {"id": str(user.id), "email": user.email, "is_active": False}


async def activate_user(db: AsyncSession, user_id: UUID) -> dict:
    """Reactivate a deactivated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", str(user_id))

    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()

    return {"id": str(user.id), "email": user.email, "is_active": True}
