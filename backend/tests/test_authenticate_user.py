"""authenticate_user — the headline login bugs (#3 lockout, #9 timing).

BUG #3 (lockout): the old code incremented failed_login_attempts then
`await db.flush()` and raised. The request's get_db dependency rolls back on a
raised exception, so the increment was DISCARDED — lockout never persisted and
brute force was unlimited. The fix commits the failed-attempt state before
raising. These tests assert commit() is actually called.

BUG #9 (timing oracle): the old code returned immediately for a non-existent
email without running bcrypt, while an existing email ran ~100ms of bcrypt —
a timing side-channel for enumerating valid admin emails. The fix runs a dummy
verify on the no-user path. This test asserts verify_password still runs.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.services import auth_service
from app.core.exceptions import UnauthorizedError
from app.models.enums import AdminActionType, UserRole


# --- lightweight fakes (no real DB / Postgres needed) ---

class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    """Records commits/flushes/added objects so tests can assert persistence."""
    def __init__(self, user=None):
        self._user = user
        self.added = []
        self.commits = 0
        self.flushes = 0

    async def execute(self, *args, **kwargs):
        return FakeResult(self._user)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def flush(self):
        self.flushes += 1

    async def rollback(self):
        pass


def make_user(**overrides):
    class U:
        pass
    u = U()
    u.id = uuid.uuid4()
    u.email = "admin@brand.com"
    u.password_hash = "irrelevant-hash"
    u.role = UserRole.ADMIN
    u.is_active = True
    u.failed_login_attempts = 0
    u.locked_until = None
    u.last_login = None
    u.must_change_password = False
    for k, v in overrides.items():
        setattr(u, k, v)
    return u


def _added_action_types(session):
    return [getattr(o, "action_type", None) for o in session.added]


# --- #9 timing oracle ---

async def test_unknown_email_runs_dummy_verify_then_raises():
    session = FakeSession(user=None)
    with patch.object(auth_service, "verify_password", return_value=False) as vp:
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(session, "ghost@nowhere.com", "pw")
    # Dummy verify must run on the no-user path to equalize timing (#9).
    vp.assert_called_once()


# --- #3 lockout persistence ---

async def test_wrong_password_persists_attempt_via_commit():
    user = make_user(failed_login_attempts=0)
    session = FakeSession(user=user)
    with patch.object(auth_service, "verify_password", return_value=False):
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(session, user.email, "wrong", ip_address="9.9.9.9")
    assert user.failed_login_attempts == 1
    # THE FIX: committed (not just flushed) so the counter survives the raise.
    assert session.commits == 1
    assert AdminActionType.FAILED_LOGIN in _added_action_types(session)


async def test_account_locks_after_max_attempts():
    user = make_user(failed_login_attempts=auth_service.MAX_FAILED_ATTEMPTS - 1)
    session = FakeSession(user=user)
    with patch.object(auth_service, "verify_password", return_value=False):
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(session, user.email, "wrong")
    assert user.failed_login_attempts == auth_service.MAX_FAILED_ATTEMPTS
    assert user.locked_until is not None
    assert session.commits == 1


async def test_locked_account_rejected_without_verifying():
    user = make_user(locked_until=datetime.now(timezone.utc) + timedelta(minutes=10))
    session = FakeSession(user=user)
    with patch.object(auth_service, "verify_password") as vp:
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(session, user.email, "whatever")
    vp.assert_not_called()


# --- success path ---

async def test_successful_login_resets_counter_and_audits():
    user = make_user(failed_login_attempts=3)
    session = FakeSession(user=user)
    with patch.object(auth_service, "verify_password", return_value=True):
        result = await auth_service.authenticate_user(session, user.email, "right", ip_address="1.2.3.4")
    assert "access_token" in result and "refresh_token" in result
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert user.last_login is not None
    assert AdminActionType.LOGIN in _added_action_types(session)
    # Success commit is handled by the get_db dependency, not the service.
    assert session.commits == 0
