from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.brand import BrandCreateRequest, BrandUpdateRequest
from app.schemas.brand_config import (
    BrandConfigUpdateRequest, ToneSettingsUpdateRequest,
    ModerationConfigUpdateRequest, ImageStyleUpdateRequest, ChatbotStatusRequest,
)
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
    """Update brand basic info (name, colors, etc). Requires brand.edit permission."""
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


# --- Brand Config Endpoints ---


@router.put("/{brand_id}/config", response_model=dict)
async def update_brand_config(
    brand_id: UUID,
    request: BrandConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update brand config (response settings, messages, lead capture, rate limits). Requires brand.config.edit."""
    await check_brand_permission(db, current_user, brand_id, "brand.config.edit")
    config = await brand_service.update_brand_config(db, brand_id, request.model_dump(exclude_unset=True))
    return api_response(data=config, message="Brand config updated")


@router.put("/{brand_id}/tone", response_model=dict)
async def update_tone_settings(
    brand_id: UUID,
    request: ToneSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tone & personality settings. Requires tone.edit."""
    await check_brand_permission(db, current_user, brand_id, "tone.edit")
    tone = await brand_service.update_tone_settings(db, brand_id, request.model_dump(exclude_unset=True))
    return api_response(data=tone, message="Tone settings updated")


@router.put("/{brand_id}/moderation", response_model=dict)
async def update_moderation_config(
    brand_id: UUID,
    request: ModerationConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update moderation config (sensitivity, allow/block lists). Requires moderation.edit."""
    await check_brand_permission(db, current_user, brand_id, "moderation.edit")
    mod = await brand_service.update_moderation_config(db, brand_id, request.model_dump(exclude_unset=True))
    return api_response(data=mod, message="Moderation config updated")


@router.put("/{brand_id}/image-styles", response_model=dict)
async def update_image_styles(
    brand_id: UUID,
    request: ImageStyleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update image style rules (card styling, UI elements). Requires image_styles.edit."""
    await check_brand_permission(db, current_user, brand_id, "image_styles.edit")
    styles = await brand_service.update_image_styles(db, brand_id, request.model_dump(exclude_unset=True))
    return api_response(data=styles, message="Image styles updated")


@router.post("/{brand_id}/emergency", response_model=dict)
async def update_chatbot_status(
    brand_id: UUID,
    request: ChatbotStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change chatbot status: normal / safe_mode / disabled. Requires emergency.override."""
    await check_brand_permission(db, current_user, brand_id, "emergency.override")
    result = await brand_service.update_chatbot_status(db, brand_id, request.status)
    return api_response(data=result, message=f"Chatbot status changed to {request.status.value}")
