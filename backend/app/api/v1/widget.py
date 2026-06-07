"""Widget config endpoint — returns brand theming for the chat widget.
Public endpoint, no auth required."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.brand import Brand
from app.models.brand_config import BrandConfig
from app.models.brand_image_style import BrandImageStyle
from app.core.exceptions import NotFoundError
from app.core.response import api_response

router = APIRouter(prefix="/widget", tags=["Widget (Public)"])


@router.get("/{brand_slug}/config", response_model=dict)
async def get_widget_config(
    brand_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get widget configuration for a brand. Public — no auth needed.
    Returns everything the chat widget needs to render: colors, logo, greeting, quick actions."""

    result = await db.execute(
        select(Brand)
        .options(
            selectinload(Brand.config),
            selectinload(Brand.image_style),
        )
        .where(Brand.slug == brand_slug, Brand.is_active == True)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", brand_slug)

    config = brand.config
    style = brand.image_style

    return api_response(data={
        "brand_name": brand.name,
        "brand_slug": brand.slug,
        "logo_url": brand.logo_url,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "greeting_message": config.greeting_message if config else None,
        "fallback_message": config.fallback_message if config else None,
        "lead_capture_trigger": config.lead_capture_trigger.value if config and config.lead_capture_trigger else None,
        "lead_capture_n_messages": config.lead_capture_n_messages if config else 3,
        "lead_show_phone_field": config.lead_show_phone_field if config else False,
        "lead_gdpr_consent_text": config.lead_gdpr_consent_text if config else None,
        "lead_allow_skip": config.lead_allow_skip if config else True,
        "image_style": {
            "product_card_edges": style.product_card_edges.value if style and style.product_card_edges else "rounded",
            "product_card_background": style.product_card_background_color if style else "#FFFFFF",
            "product_card_overlay": style.product_card_overlay_style.value if style and style.product_card_overlay_style else "none",
            "ui_button_style": style.ui_button_style.value if style and style.ui_button_style else "rounded",
            "ui_button_color": style.ui_button_color if style else brand.primary_color,
            "ui_card_background": style.ui_card_background if style else "#FFFFFF",
        } if style else None,
        "quick_actions": ["Browse Products", "Skin Quiz", "FAQ"],
    })
