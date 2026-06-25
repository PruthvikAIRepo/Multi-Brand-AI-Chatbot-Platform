"""Refresh-token rotation + reuse detection (#2) and the forgot-password flow
that backs the Super-Admin reset endpoint (#4).

BEFORE: /auth/refresh returned a new access token only — the refresh token never
rotated, so a leaked refresh token stayed valid for its full 7-day life with no
way to detect replay. Now each refresh rotates (old token revoked, new issued) and
a revoked token presented again triggers revocation of ALL the user's tokens.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services import auth_service
from app.core.exceptions import UnauthorizedError
from app.models.enums import UserRole


class FakeResult:
    def __init__(self, scalar=None, items=None):
        self._scalar = scalar
        self._items = items or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._items


class FakeSession:
    def __init__(self, scalar=None, items=None):
        self._scalar = scalar
        self._items = items or []
        self.added = []
        self.commits = 0
        self.flushes = 0

    async def execute(self, *a, **k):
        return FakeResult(self._scalar, self._items)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def flush(self):
        self.flushes += 1


def stub_user(is_active=True):
    class U:
        pass
    u = U()
    u.id = uuid.uuid4()
    u.email = "admin@brand.com"
    u.role = UserRole.ADMIN
    u.is_active = is_active
    return u


def stub_refresh_token(*, revoked=False, expired=False, user=None):
    class T:
        pass
    t = T()
    user = user or stub_user()
    t.token_hash = "hash"
    t.revoked = revoked
    t.expires_at = datetime.now(timezone.utc) + timedelta(days=(-1 if expired else 7))
    t.user = user
    t.user_id = user.id
    return t


# --- refresh rotation (#2) ---

async def test_refresh_rotates_tokens_and_revokes_old():
    token = stub_refresh_token()
    session = FakeSession(scalar=token)
    result = await auth_service.refresh_access_token(session, "raw-refresh")
    assert "access_token" in result and "refresh_token" in result
    assert token.revoked is True                 # old token rotated out
    assert len(session.added) == 1               # a new refresh token was stored
    assert session.commits == 0                  # commit handled by get_db on success


async def test_refresh_rejects_unknown_token():
    session = FakeSession(scalar=None)
    with pytest.raises(UnauthorizedError):
        await auth_service.refresh_access_token(session, "nope")


async def test_refresh_reuse_detection_revokes_all():
    user = stub_user()
    presented = stub_refresh_token(revoked=True, user=user)   # already revoked => reuse
    others = [stub_refresh_token(user=user), stub_refresh_token(user=user)]
    session = FakeSession(scalar=presented, items=others)
    with pytest.raises(UnauthorizedError):
        await auth_service.refresh_access_token(session, "stolen")
    assert all(t.revoked for t in others)        # every active token nuked
    assert session.commits == 1                  # persisted before raising


async def test_refresh_rejects_expired_token():
    session = FakeSession(scalar=stub_refresh_token(expired=True))
    with pytest.raises(UnauthorizedError):
        await auth_service.refresh_access_token(session, "old")


async def test_refresh_rejects_inactive_user():
    session = FakeSession(scalar=stub_refresh_token(user=stub_user(is_active=False)))
    with pytest.raises(UnauthorizedError):
        await auth_service.refresh_access_token(session, "tok")


# --- forgot_password backs the Super-Admin reset endpoint (#4) ---

async def test_forgot_password_active_user_creates_token_and_emails():
    user = stub_user(is_active=True)
    session = FakeSession(scalar=user, items=[])
    with patch("app.services.email_service.send_password_reset_email",
               new=AsyncMock(return_value=True)) as send:
        raw = await auth_service.forgot_password(session, user.email)
    assert raw is not None
    assert len(session.added) == 1               # a PasswordResetToken was created
    send.assert_awaited_once()


async def test_forgot_password_unknown_user_returns_none_and_no_email():
    session = FakeSession(scalar=None)
    with patch("app.services.email_service.send_password_reset_email",
               new=AsyncMock()) as send:
        assert await auth_service.forgot_password(session, "ghost@x.com") is None
    send.assert_not_awaited()


async def test_forgot_password_inactive_user_returns_none():
    session = FakeSession(scalar=stub_user(is_active=False))
    with patch("app.services.email_service.send_password_reset_email", new=AsyncMock()):
        assert await auth_service.forgot_password(session, "x@x.com") is None
