from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.brand import BrandCreateRequest, BrandUpdateRequest
from app.services import brand_service
from app.core.permissions import get_current_user, require_super_admin, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.post("", response_model=dict)
async def create_brand(
    request: BrandCreateRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new brand with default configs. Super Admin only."""
    brand = await brand_service.create_brand(db, request.model_dump())
    return api_response(data=brand, message="Brand created successfully")


@router.get("", response_model=dict)
async def list_brands(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all brands with pagination. Super Admin sees all, Admin sees assigned only."""
    brands, total = await brand_service.list_brands(db, current_user, page, per_page)
    return paginated_response(data=brands, total=total, page=page, per_page=per_page)


@router.get("/{brand_id}", response_model=dict)
async def get_brand(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get brand details with all configs. Requires brand.view permission."""
    await check_brand_permission(db, current_user, brand_id, "brand.view")
    brand = await brand_service.get_brand(db, brand_id)
    return api_response(data=brand)


@router.put("/{brand_id}", response_model=dict)
async def update_brand(
    brand_id: UUID,
    request: BrandUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update brand details. Requires brand.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "brand.edit")
    brand = await brand_service.update_brand(
        db, brand_id, request.model_dump(exclude_unset=True)
    )
    return api_response(data=brand, message="Brand updated successfully")


@router.delete("/{brand_id}", response_model=dict)
async def delete_brand(
    brand_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a brand and ALL related data. Super Admin only. Irreversible."""
    await brand_service.delete_brand(db, brand_id)
    return api_response(message="Brand deleted successfully")
