from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import secret_service
from app.core.permissions import require_super_admin
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import SecretType

router = APIRouter(prefix="/secrets", tags=["Secret Management"])


class SecretCreateRequest(BaseModel):
    brand_id: UUID | None = None  # None = system default
    secret_type: SecretType
    value: str = Field(..., min_length=1)


class SecretUpdateRequest(BaseModel):
    value: str = Field(..., min_length=1)


@router.post("", response_model=dict)
async def create_secret(
    request: SecretCreateRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a new secret (API key, token). Super Admin only. Value encrypted immediately."""
    secret = await secret_service.create_secret(
        db, request.brand_id, request.secret_type, request.value
    )
    return api_response(data=secret, message="Secret added securely")


@router.get("", response_model=dict)
async def list_secrets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all secrets with masked values. Never returns plaintext. Super Admin only."""
    secrets, total = await secret_service.list_secrets(db, page, per_page, brand_id)
    return paginated_response(data=secrets, total=total, page=page, per_page=per_page)


@router.put("/{secret_id}", response_model=dict)
async def update_secret(
    secret_id: UUID,
    request: SecretUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Replace a secret value. Old value is never visible. Super Admin only."""
    secret = await secret_service.update_secret(db, secret_id, request.value)
    return api_response(data=secret, message="Secret updated")


@router.delete("/{secret_id}", response_model=dict)
async def delete_secret(
    secret_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a secret. Super Admin only."""
    await secret_service.delete_secret(db, secret_id)
    return api_response(message="Secret deleted")


@router.post("/{secret_id}/test", response_model=dict)
async def test_secret(
    secret_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test if a secret is valid (decryptable, non-empty). Does NOT reveal the value. Super Admin only."""
    result = await secret_service.test_secret(db, secret_id)
    return api_response(data=result)
