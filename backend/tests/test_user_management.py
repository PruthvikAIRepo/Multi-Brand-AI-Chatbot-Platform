"""User-management service — Unit 2 (unlock + before-state for audit).

These verify the service-level behavior that feeds the audit trail (IP + before/after
state is added at the route layer): unlock clears a lockout, and deactivate/activate
report their previous active state so the audit log can record before/after.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services import user_service
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
    def __init__(self, user=None):
        self._user = user
        self.flushes = 0

    async def execute(self, *args, **kwargs):
        # User lookups use scalar_one_or_none; the token sweep uses scalars().all() -> [].
        return FakeResult(scalar=self._user, items=[])

    async def flush(self):
        self.flushes += 1


def make_user(**overrides):
    class U:
        pass
    u = U()
    u.id = uuid.uuid4()
    u.email = "admin@brand.com"
    u.role = UserRole.ADMIN
    u.is_active = True
    u.failed_login_attempts = 0
    u.locked_until = None
    for k, v in overrides.items():
        setattr(u, k, v)
    return u


async def test_unlock_clears_lockout_and_reports_was_locked():
    user = make_user(failed_login_attempts=5,
                     locked_until=datetime.now(timezone.utc) + timedelta(minutes=10))
    result = await user_service.unlock_user(FakeSession(user), user.id)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert result["was_locked"] is True


async def test_unlock_on_unlocked_account_reports_false():
    user = make_user()
    result = await user_service.unlock_user(FakeSession(user), user.id)
    assert result["was_locked"] is False


async def test_deactivate_reports_before_state():
    user = make_user(is_active=True)
    result = await user_service.deactivate_user(FakeSession(user), user.id, uuid.uuid4())
    assert result["before_is_active"] is True
    assert result["is_active"] is False
    assert user.is_active is False


async def test_cannot_deactivate_self():
    user = make_user()
    from app.core.exceptions import BadRequestError
    with pytest.raises(BadRequestError):
        # same id for target and current user
        await user_service.deactivate_user(FakeSession(user), user.id, user.id)


async def test_activate_reports_before_state_and_clears_lock():
    user = make_user(is_active=False, failed_login_attempts=3,
                     locked_until=datetime.now(timezone.utc) + timedelta(minutes=5))
    result = await user_service.activate_user(FakeSession(user), user.id)
    assert result["before_is_active"] is False
    assert result["is_active"] is True
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
