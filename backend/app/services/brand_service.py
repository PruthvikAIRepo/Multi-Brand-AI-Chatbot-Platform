import re
from uuid import UUID
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.brand import Brand
from app.models.brand_config import BrandConfig
from app.models.tone_setting import ToneSetting
from app.models.brand_image_style import BrandImageStyle
from app.models.moderation_config import ModerationConfig
from app.models.product import Product
from app.models.user import User
from app.core.exceptions import NotFoundError, AlreadyExistsError, BadRequestError
from app.core.permissions import get_user_brand_ids


def _generate_slug(name: str) -> str:
    """Generate URL-safe slug from brand name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


async def _ensure_unique_slug(db: AsyncSession, slug: str, exclude_id: UUID | None = None) -> str:
    """Ensure slug is unique, append number if needed. Max 100 attempts."""
    base_slug = slug
    counter = 1
    while counter <= 100:
        query = select(Brand).where(Brand.slug == slug)
        if exclude_id:
            query = query.where(Brand.id != exclude_id)
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
    raise BadRequestError("Unable to generate unique slug. Try a different brand name.")


async def create_brand(db: AsyncSession, data: dict) -> dict:
    """Create a new brand with all default config tables."""
    slug = data.get("slug") or _generate_slug(data["name"])
    slug = await _ensure_unique_slug(db, slug)

    # Check name uniqueness
    result = await db.execute(select(Brand).where(Brand.name == data["name"]))
    if result.scalar_one_or_none():
        raise AlreadyExistsError("Brand", "name", data["name"])

    brand = Brand(
        name=data["name"],
        slug=slug,
        logo_url=data.get("logo_url"),
        primary_color=data.get("primary_color"),
        secondary_color=data.get("secondary_color"),
        accent_color=data.get("accent_color"),
        description=data.get("description"),
        currency=data.get("currency", "INR"),
    )
    db.add(brand)
    await db.flush()

    # Auto-create config tables with defaults
    db.add(BrandConfig(brand_id=brand.id))
    db.add(ToneSetting(brand_id=brand.id))
    db.add(BrandImageStyle(brand_id=brand.id))
    db.add(ModerationConfig(brand_id=brand.id))
    await db.flush()

    return _brand_to_dict(brand, product_count=0)


async def list_brands(
    db: AsyncSession, current_user: User, page: int = 1, per_page: int = 20
) -> tuple[list[dict], int]:
    """List brands with product counts. Paginated, filtered by role."""
    # Base filter
    brand_ids = get_user_brand_ids(current_user)
    base_filter = Brand.id.in_(brand_ids) if brand_ids is not None else True

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Brand).where(base_filter)
    )
    total = count_result.scalar()

    # Fetch brands with product count in single query (no N+1)
    product_count_subq = (
        select(
            Product.brand_id,
            func.count(Product.id).label("product_count"),
        )
        .where(Product.deleted_at.is_(None))
        .group_by(Product.brand_id)
        .subquery()
    )

    result = await db.execute(
        select(Brand, func.coalesce(product_count_subq.c.product_count, 0).label("product_count"))
        .outerjoin(product_count_subq, Brand.id == product_count_subq.c.brand_id)
        .where(base_filter)
        .order_by(Brand.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    brand_list = []
    for brand, product_count in result.all():
        brand_list.append(_brand_to_dict(brand, product_count))

    return brand_list, total


async def get_brand(db: AsyncSession, brand_id: UUID) -> dict:
    """Get a single brand with full details and all configs."""
    result = await db.execute(
        select(Brand)
        .options(
            selectinload(Brand.config),
            selectinload(Brand.tone_setting),
            selectinload(Brand.image_style),
            selectinload(Brand.moderation_config),
        )
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", str(brand_id))

    # Product count
    count_result = await db.execute(
        select(func.count()).select_from(Product).where(
            Product.brand_id == brand.id,
            Product.deleted_at.is_(None),
        )
    )
    product_count = count_result.scalar()

    brand_dict = _brand_to_dict(brand, product_count)

    if brand.config:
        brand_dict["config"] = _config_to_dict(brand.config)
    if brand.tone_setting:
        brand_dict["tone_settings"] = _tone_to_dict(brand.tone_setting)
    if brand.image_style:
        brand_dict["image_styles"] = _image_style_to_dict(brand.image_style)
    if brand.moderation_config:
        brand_dict["moderation_config"] = _moderation_to_dict(brand.moderation_config)

    return brand_dict


async def update_brand(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Update brand basic info. Supports setting fields to null."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", str(brand_id))

    # Check name uniqueness if name is being changed
    if "name" in data and data["name"] and data["name"] != brand.name:
        existing = await db.execute(
            select(Brand).where(Brand.name == data["name"], Brand.id != brand_id)
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsError("Brand", "name", data["name"])
        brand.name = data["name"]
        brand.slug = await _ensure_unique_slug(db, _generate_slug(data["name"]), brand_id)

    # Update fields — allows setting to None (e.g., clearing logo_url)
    for field in ["logo_url", "primary_color", "secondary_color", "accent_color", "description", "currency", "is_active"]:
        if field in data:
            setattr(brand, field, data[field])

    await db.flush()

    # Get product count for response
    count_result = await db.execute(
        select(func.count()).select_from(Product).where(
            Product.brand_id == brand.id,
            Product.deleted_at.is_(None),
        )
    )
    product_count = count_result.scalar()

    return _brand_to_dict(brand, product_count)


async def update_brand_config(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Update brand config (response settings, messages, lead capture, etc.)."""
    result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand_id))
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("Brand config", str(brand_id))

    for field, value in data.items():
        setattr(config, field, value)
    await db.flush()
    return _config_to_dict(config)


async def update_tone_settings(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Update tone settings (emotional style, vocabulary, micro-tone rules)."""
    result = await db.execute(select(ToneSetting).where(ToneSetting.brand_id == brand_id))
    tone = result.scalar_one_or_none()
    if not tone:
        raise NotFoundError("Tone settings", str(brand_id))

    for field, value in data.items():
        setattr(tone, field, value)
    await db.flush()
    return _tone_to_dict(tone)


async def update_moderation_config(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Update moderation config (sensitivity, allow/block lists)."""
    result = await db.execute(select(ModerationConfig).where(ModerationConfig.brand_id == brand_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise NotFoundError("Moderation config", str(brand_id))

    for field, value in data.items():
        setattr(mod, field, value)
    await db.flush()
    return _moderation_to_dict(mod)


async def update_image_styles(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Update image style rules (card styling, UI elements)."""
    result = await db.execute(select(BrandImageStyle).where(BrandImageStyle.brand_id == brand_id))
    style = result.scalar_one_or_none()
    if not style:
        raise NotFoundError("Image styles", str(brand_id))

    for field, value in data.items():
        setattr(style, field, value)
    await db.flush()
    return _image_style_to_dict(style)


async def update_chatbot_status(db: AsyncSession, brand_id: UUID, status) -> dict:
    """Change chatbot status: normal / safe_mode / disabled (emergency override)."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", str(brand_id))

    brand.chatbot_status = status
    await db.flush()
    return {"brand_id": str(brand_id), "chatbot_status": brand.chatbot_status.value}


async def delete_brand(db: AsyncSession, brand_id: UUID) -> None:
    """Delete a brand and all related data (CASCADE). Irreversible."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", str(brand_id))

    await db.delete(brand)
    await db.flush()


# --- Helper functions ---

def _brand_to_dict(brand: Brand, product_count: int = 0) -> dict:
    return {
        "id": str(brand.id),
        "name": brand.name,
        "slug": brand.slug,
        "logo_url": brand.logo_url,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "description": brand.description,
        "currency": brand.currency,
        "chatbot_status": brand.chatbot_status.value if brand.chatbot_status else "normal",
        "is_active": brand.is_active,
        "product_count": product_count,
        "created_at": brand.created_at.isoformat(),
        "updated_at": brand.updated_at.isoformat(),
    }


def _config_to_dict(config: BrandConfig) -> dict:
    return {
        "response_length": config.response_length.value if config.response_length else "medium",
        "max_tokens": config.max_tokens,
        "rag_similarity_threshold": config.rag_similarity_threshold,
        "recommendation_top_n": config.recommendation_top_n,
        "session_timeout_minutes": config.session_timeout_minutes,
        "greeting_message": config.greeting_message,
        "signoff_message": config.signoff_message,
        "fallback_message": config.fallback_message,
        "fallback_tone_profile": config.fallback_tone_profile,
        "no_medical_claims": config.no_medical_claims,
        "no_over_explaining": config.no_over_explaining,
        "no_aggressive_upselling": config.no_aggressive_upselling,
        "no_unnecessary_details": config.no_unnecessary_details,
        "no_medical_tone": config.no_medical_tone,
        "rate_limit_per_user": config.rate_limit_per_user,
        "conversation_retention_days": config.conversation_retention_days,
        "lead_capture_trigger": config.lead_capture_trigger.value if config.lead_capture_trigger else "after_n_messages",
        "lead_capture_n_messages": config.lead_capture_n_messages,
        "lead_show_phone_field": config.lead_show_phone_field,
        "lead_gdpr_consent_text": config.lead_gdpr_consent_text,
        "lead_allow_skip": config.lead_allow_skip,
    }


def _tone_to_dict(tone: ToneSetting) -> dict:
    return {
        "emotional_style": tone.emotional_style.value if tone.emotional_style else "warm",
        "communication_style": tone.communication_style.value if tone.communication_style else "casual",
        "emoji_usage": tone.emoji_usage,
        "vocabulary_preferred": tone.vocabulary_preferred or [],
        "vocabulary_avoided": tone.vocabulary_avoided or [],
        "softness_level": tone.softness_level.value if tone.softness_level else "gentle",
        "sensory_language_enabled": tone.sensory_language_enabled,
        "emotional_cues": tone.emotional_cues or [],
        "restricted_adjectives": tone.restricted_adjectives or [],
        "clinical_language_allowed": tone.clinical_language_allowed,
        "harsh_word_blocking": tone.harsh_word_blocking,
    }


def _image_style_to_dict(style: BrandImageStyle) -> dict:
    return {
        "image_style_profile": style.image_style_profile.value if style.image_style_profile else "modern_clean",
        "product_card_edges": style.product_card_edges.value if style.product_card_edges else "rounded",
        "product_card_background_color": style.product_card_background_color,
        "product_card_overlay_style": style.product_card_overlay_style.value if style.product_card_overlay_style else "none",
        "routine_card_edges": style.routine_card_edges.value if style.routine_card_edges else "rounded",
        "routine_card_background_color": style.routine_card_background_color,
        "routine_card_overlay_style": style.routine_card_overlay_style.value if style.routine_card_overlay_style else "none",
        "ui_button_style": style.ui_button_style.value if style.ui_button_style else "rounded",
        "ui_button_color": style.ui_button_color,
        "ui_card_background": style.ui_card_background,
    }


def _moderation_to_dict(mod: ModerationConfig) -> dict:
    return {
        "sensitivity": mod.sensitivity.value if mod.sensitivity else "medium",
        "response_on_block": mod.response_on_block.value if mod.response_on_block else "brand_fallback",
        "allow_list": mod.allow_list or [],
        "block_list": mod.block_list or [],
        "prompt_injection_patterns": mod.prompt_injection_patterns or [],
    }
