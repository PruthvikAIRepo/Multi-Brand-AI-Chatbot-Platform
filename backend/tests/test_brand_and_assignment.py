"""Brand + admin-assignment logic changes.

- Brand assignment is now OPTIONAL at admin creation (SRS §21.4 / UI §23).
- Default currency is USD.
- Brand config/update schemas reject unknown fields (extra=forbid) — protects the
  service-layer setattr loops.
- `is_active` is no longer editable via the general brand update (it's a
  Super-Admin-only activate/deactivate action).
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.schemas.brand import BrandCreateRequest, BrandUpdateRequest
from app.schemas.brand_config import BrandConfigUpdateRequest
from app.services import user_service
from app.models.enums import UserRole
from app.core.exceptions import BadRequestError


# --- schema behavior ---

def test_brand_default_currency_is_usd():
    assert BrandCreateRequest(name="Acme").currency == "USD"


def test_brand_currency_can_be_overridden():
    assert BrandCreateRequest(name="Acme", currency="EUR").currency == "EUR"


def test_brand_config_update_rejects_unknown_field():
    # extra=forbid protects the service-layer blind setattr loop.
    with pytest.raises(ValidationError):
        BrandConfigUpdateRequest(not_a_real_field=1)


def test_brand_update_rejects_is_active():
    # Activation is Super-Admin-only via /brands/{id}/activate|deactivate — not here.
    with pytest.raises(ValidationError):
        BrandUpdateRequest(is_active=False)


# --- invite: brand assignment is optional ---

class FakeResult:
    def scalar_one_or_none(self):
        return None  # email does not already exist


class FakeSession:
    def __init__(self):
        self.added = []

    async def execute(self, *a, **k):
        return FakeResult()

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass


async def test_invite_admin_allows_no_brands():
    session = FakeSession()
    with patch("app.services.email_service.send_invitation_email",
               new=AsyncMock(return_value=True)) as send:
        result = await user_service.invite_user(
            session, "new.admin@example.com", "New Admin", UserRole.ADMIN, []
        )
    assert result["assigned_brand_ids"] == []      # created with no brand (parked)
    assert result["role"] == "admin"
    send.assert_awaited_once()                       # invitation email still sent


async def test_invite_superadmin_still_blocked():
    with pytest.raises(BadRequestError):
        await user_service.invite_user(
            FakeSession(), "x@example.com", "X", UserRole.SUPER_ADMIN, []
        )
