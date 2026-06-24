"""must_change_password enforcement gate — Step 1 hardening.

BUG (before the fix): must_change_password was set on seed/invite but NEVER
enforced, so a freshly-created account could use the whole API on its initial
password. Now get_current_user (which require_super_admin / require_brand_access
build on) rejects any user that still has the flag set.
"""
import pytest

from app.core.permissions import get_current_user, get_authenticated_user
from app.core.exceptions import ForbiddenError


class StubUser:
    def __init__(self, must_change: bool):
        self.must_change_password = must_change


async def test_blocks_user_that_must_change_password():
    with pytest.raises(ForbiddenError):
        # Called directly with the resolved user (FastAPI's Depends default is
        # only used at request time).
        await get_current_user(user=StubUser(must_change=True))


async def test_allows_user_once_password_changed():
    user = StubUser(must_change=False)
    assert await get_current_user(user=user) is user


def test_escape_hatch_dependency_is_distinct():
    # The lenient dependency must NOT be the same callable as the enforced one,
    # otherwise change-password would be unreachable while gated.
    assert get_authenticated_user is not get_current_user
