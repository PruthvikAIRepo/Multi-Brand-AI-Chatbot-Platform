"""Seed the first Super Admin account.

Credentials are read from the environment (never hardcoded):
    SUPERADMIN_EMAIL      e.g. owner@yourbrand.com
    SUPERADMIN_PASSWORD   must meet the password strength policy

Usage:
    cd backend
    source venv/Scripts/activate
    SUPERADMIN_EMAIL=... SUPERADMIN_PASSWORD=... python -m app.seed

The created account has must_change_password=True, so the owner is forced
to set a new password on first login before any other action is allowed.
"""
import asyncio
import sys

from sqlalchemy import select

from app.config import get_settings
from app.db.session import async_session_factory
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password
from app.schemas.auth import _validate_password_strength


async def seed_super_admin() -> None:
    settings = get_settings()
    email = (settings.SUPERADMIN_EMAIL or "").strip().lower()
    password = settings.SUPERADMIN_PASSWORD or ""

    # Fail closed: refuse to run without explicit credentials.
    if not email or not password:
        print(
            "ERROR: SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must both be set.\n"
            "       Set them in the environment, then re-run: python -m app.seed",
            file=sys.stderr,
        )
        sys.exit(1)

    if "@" not in email:
        print(f"ERROR: SUPERADMIN_EMAIL '{email}' is not a valid email.", file=sys.stderr)
        sys.exit(1)

    # Enforce the same password policy the API enforces.
    try:
        _validate_password_strength(password)
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
    except ValueError as exc:
        print(f"ERROR: SUPERADMIN_PASSWORD rejected: {exc}", file=sys.stderr)
        sys.exit(1)

    async with async_session_factory() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

        if existing:
            print(f"Super Admin already exists: {email} (no changes made)")
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            must_change_password=True,
        )
        session.add(user)
        await session.commit()

        print(f"Super Admin created: {email}")
        print("  must_change_password=True — set a new password on first login.")


if __name__ == "__main__":
    asyncio.run(seed_super_admin())
