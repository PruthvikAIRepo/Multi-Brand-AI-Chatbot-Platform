"""Auth rate limiting — issue #8.

BUG (before the fix): no rate limiting existed on auth routes at all. The new
check_auth_rate_limit gates login/forgot/reset per IP and, importantly, FAILS
OPEN if Redis is unavailable so an outage can't lock everyone out of login.
"""
from unittest.mock import AsyncMock, patch

from app.core import rate_limiter


async def test_none_ip_is_allowed():
    # No IP (e.g. missing header) should not block.
    assert await rate_limiter.check_auth_rate_limit(None) is None


async def test_fails_open_when_redis_errors():
    with patch.object(rate_limiter, "check_rate_limit",
                      new=AsyncMock(side_effect=RuntimeError("redis down"))):
        assert await rate_limiter.check_auth_rate_limit("1.2.3.4") is None


async def test_allows_when_under_limit():
    with patch.object(rate_limiter, "check_rate_limit",
                      new=AsyncMock(return_value={"allowed": True, "remaining": 5, "reset_in": 30})):
        assert await rate_limiter.check_auth_rate_limit("1.2.3.4") is None


async def test_blocks_when_over_limit():
    with patch.object(rate_limiter, "check_rate_limit",
                      new=AsyncMock(return_value={"allowed": False, "remaining": 0, "reset_in": 42})):
        result = await rate_limiter.check_auth_rate_limit("1.2.3.4")
        assert result is not None
        assert result["reset_in"] == 42
