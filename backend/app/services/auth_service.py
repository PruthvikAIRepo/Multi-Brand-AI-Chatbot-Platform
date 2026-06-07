from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User, RefreshToken, PasswordResetToken
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    hash_token, generate_reset_token,
)
from app.core.exceptions import UnauthorizedError, BadRequestError, NotFoundError
from app.config import get_settings

settings = get_settings()

# Brute-force protection constants
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


async def authenticate_user(db: AsyncSession, email: str, password: str) -> dict:
    """Login flow with brute-force protection."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("Invalid email or password")

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
        raise UnauthorizedError(f"Account locked. Try again in {remaining} minutes.")

    # Check if account is active
    if not user.is_active:
        raise UnauthorizedError("Account has been deactivated")

    # Verify password
    if not verify_password(password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        await db.flush()
        raise UnauthorizedError("Invalid email or password")

    # Successful login — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)

    # Generate tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    })

    raw_refresh, refresh_hash = create_refresh_token()

    # Store refresh token in DB
    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token_obj)
    await db.flush()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
    }


async def refresh_access_token(db: AsyncSession, raw_refresh_token: str) -> dict:
    """Generate new access token using a valid refresh token."""
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise UnauthorizedError("Invalid or expired refresh token")

    if not refresh_token.user.is_active:
        raise UnauthorizedError("Account has been deactivated")

    # Generate new access token
    access_token = create_access_token({
        "sub": str(refresh_token.user.id),
        "email": refresh_token.user.email,
        "role": refresh_token.user.role.value,
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


async def change_password(db: AsyncSession, user_id: UUID, current_password: str, new_password: str) -> None:
    """Change password for authenticated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User")

    if not verify_password(current_password, user.password_hash):
        raise BadRequestError("Current password is incorrect")

    if current_password == new_password:
        raise BadRequestError("New password must be different from current password")

    user.password_hash = hash_password(new_password)
    user.must_change_password = False

    # Revoke all existing refresh tokens (force re-login on other devices)
    await _revoke_all_refresh_tokens(db, user.id)
    await db.flush()


async def forgot_password(db: AsyncSession, email: str) -> str | None:
    """Generate password reset token. Returns raw token if user exists, None otherwise.
    Always return success to the client to prevent email enumeration."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    # Invalidate any existing reset tokens for this user
    existing = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        )
    )
    for token in existing.scalars().all():
        token.used = True

    # Generate new reset token
    raw_token, token_hash = generate_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.flush()

    return raw_token


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    """Reset password using a valid reset token."""
    token_hash = hash_token(raw_token)

    result = await db.execute(
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise BadRequestError("Invalid or expired reset token")

    # Update password
    reset_token.user.password_hash = hash_password(new_password)
    reset_token.user.must_change_password = False
    reset_token.used = True

    # Revoke all refresh tokens
    await _revoke_all_refresh_tokens(db, reset_token.user.id)
    await db.flush()


async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a specific refresh token (logout from current device)."""
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        refresh_token.revoked = True
        await db.flush()


async def _revoke_all_refresh_tokens(db: AsyncSession, user_id: UUID) -> None:
    """Revoke all refresh tokens for a user (used on password change/reset)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
    )
    for token in result.scalars().all():
        token.revoked = True
