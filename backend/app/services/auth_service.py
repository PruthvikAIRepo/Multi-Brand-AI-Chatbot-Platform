from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select, delete
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
from app.services import audit_service
from app.models.enums import AdminActionType

settings = get_settings()

# Brute-force protection constants
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Pre-computed bcrypt hash used to equalize response time when the email does
# not exist, so login timing can't be used to enumerate valid accounts.
_DUMMY_PASSWORD_HASH = hash_password("timing-equalizer-not-a-real-account")


async def authenticate_user(
    db: AsyncSession, email: str, password: str, ip_address: str | None = None
) -> dict:
    """Login flow with brute-force protection and audit logging.

    ip_address is recorded on the audit trail (SRS 21.3). Failed-attempt state
    is committed before raising so account lockout actually persists (the
    request's get_db dependency rolls back on the raised exception)."""
    email = (email or "").strip().lower()

    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Equalize timing against the password-verify path to prevent
        # email enumeration; then fail with the same generic message.
        verify_password(password, _DUMMY_PASSWORD_HASH)
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
        # Increment failed attempts and lock if threshold reached.
        user.failed_login_attempts += 1
        locked = user.failed_login_attempts >= MAX_FAILED_ATTEMPTS
        if locked:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        await audit_service.log_action(
            db, user.id, AdminActionType.FAILED_LOGIN, "auth",
            ip_address=ip_address,
            after_state={"failed_login_attempts": user.failed_login_attempts, "locked": locked},
        )
        # Commit now so the counter/lock survive — get_db rolls back on raise.
        await db.commit()
        raise UnauthorizedError("Invalid email or password")

    # Successful login — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    await audit_service.log_action(
        db, user.id, AdminActionType.LOGIN, "auth", ip_address=ip_address,
    )

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
    """Exchange a refresh token for a new access token AND a new refresh token
    (rotation), revoking the presented token. Includes reuse detection: if an
    already-revoked token is presented (a sign of theft/replay), ALL of the
    user's refresh tokens are revoked, forcing a fresh login."""
    token_hash = hash_token(raw_refresh_token)

    # Look up WITHOUT the revoked filter so a revoked token can be detected as reuse.
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise UnauthorizedError("Invalid or expired refresh token")

    # Reuse detection: a revoked token presented again => likely compromised.
    if refresh_token.revoked:
        await _revoke_all_refresh_tokens(db, refresh_token.user_id)
        # Commit the mass-revocation before raising (get_db rolls back on raise).
        await db.commit()
        raise UnauthorizedError("Refresh token reuse detected. Please log in again.")

    if refresh_token.expires_at <= datetime.now(timezone.utc):
        raise UnauthorizedError("Invalid or expired refresh token")

    if not refresh_token.user.is_active:
        raise UnauthorizedError("Account has been deactivated")

    # Rotate: revoke the presented token and issue a fresh refresh token.
    refresh_token.revoked = True

    access_token = create_access_token({
        "sub": str(refresh_token.user.id),
        "email": refresh_token.user.email,
        "role": refresh_token.user.role.value,
    })
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        user_id=refresh_token.user_id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    await db.flush()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
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

    # Send reset email AFTER token is persisted
    from app.services.email_service import send_password_reset_email
    await send_password_reset_email(email, raw_token)

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
    """Log out from the current device by DELETING the refresh token.

    We delete (rather than flag revoked) so a later refresh attempt with this
    token reads as a plain 'invalid/expired' token instead of tripping reuse
    detection — reuse detection must fire only for replayed *rotated* tokens."""
    token_hash = hash_token(raw_refresh_token)
    await db.execute(delete(RefreshToken).where(RefreshToken.token_hash == token_hash))
    await db.flush()


async def _revoke_all_refresh_tokens(db: AsyncSession, user_id: UUID) -> None:
    """DELETE all of a user's refresh tokens (logout-all on password change/reset
    and on reuse detection). Deleting keeps these benign/forced invalidations
    distinct from the single revoked-but-present row a rotation leaves behind as
    the reuse tripwire (see refresh_access_token)."""
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
