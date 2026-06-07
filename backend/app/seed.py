"""Seed the first Super Admin account.

Usage:
    cd backend
    source venv/Scripts/activate
    python -m app.seed
"""
import asyncio
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password


async def seed_super_admin():
    email = "admin@chatbot.com"
    password = "Admin@123"

    async with async_session_factory() as session:
        # Check if Super Admin already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Super Admin already exists: {email}")
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
        print(f"Super Admin created successfully!")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  (You will be asked to change password on first login)")


if __name__ == "__main__":
    asyncio.run(seed_super_admin())
