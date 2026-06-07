from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import bot_protection_service
from app.core.permissions import require_super_admin
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/bot-protection", tags=["Bot Protection"])


class BlockIPRequest(BaseModel):
    ip_address: str
    brand_id: UUID | None = None
    reason: str | None = None


class BlockUserRequest(BaseModel):
    user_identifier: str
    brand_id: UUID | None = None
    reason: str | None = None


@router.post("/ip", response_model=dict)
async def block_ip(
    request: BlockIPRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Block an IP address. Super Admin only."""
    result = await bot_protection_service.block_ip(
        db, request.ip_address, request.brand_id, current_user.id, request.reason
    )
    return api_response(data=result, message="IP blocked")


@router.get("/ip", response_model=dict)
async def list_blocked_ips(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List blocked IPs. Super Admin only."""
    data, total = await bot_protection_service.list_blocked_ips(db, page, per_page, brand_id)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.delete("/ip/{entry_id}", response_model=dict)
async def unblock_ip(
    entry_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unblock an IP. Super Admin only."""
    await bot_protection_service.unblock_ip(db, entry_id)
    return api_response(message="IP unblocked")


@router.post("/users", response_model=dict)
async def block_user_identifier(
    request: BlockUserRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Block a user identifier. Super Admin only."""
    result = await bot_protection_service.block_user(
        db, request.user_identifier, request.brand_id, current_user.id, request.reason
    )
    return api_response(data=result, message="User blocked")


@router.get("/users", response_model=dict)
async def list_blocked_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List blocked users. Super Admin only."""
    data, total = await bot_protection_service.list_blocked_users(db, page, per_page, brand_id)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.delete("/users/{entry_id}", response_model=dict)
async def unblock_user(
    entry_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unblock a user. Super Admin only."""
    await bot_protection_service.unblock_user(db, entry_id)
    return api_response(message="User unblocked")
