"""Chat endpoint — the public-facing API that users interact with.
No admin auth required — this is for end users via the chat widget."""

import uuid
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import chat_service
from app.core.response import api_response
from app.core.rate_limiter import check_chat_rate_limit
from app.core.exceptions import RateLimitError
from app.models.enums import ChannelType

router = APIRouter(prefix="/chat", tags=["Chat (Public)"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    channel: ChannelType = ChannelType.WEBSITE


@router.post("/{brand_slug}", response_model=dict)
async def send_message(
    brand_slug: str,
    request: ChatMessageRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a brand's chatbot. Public endpoint — no auth needed.
    Rate limited per IP and per session. Full pipeline: moderation → RAG → LLM → compliance."""

    from sqlalchemy import select
    from app.models.brand import Brand
    from app.models.brand_config import BrandConfig

    # Resolve brand
    result = await db.execute(select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True))
    brand = result.scalar_one_or_none()
    if not brand:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Brand", brand_slug)

    # Get rate limit config
    config_result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand.id))
    config = config_result.scalar_one_or_none()
    per_user_limit = config.rate_limit_per_user if config else 30

    # Generate session_id
    session_id = request.session_id or f"web_{uuid.uuid4().hex[:16]}"

    # Rate limiting
    client_ip = raw_request.client.host if raw_request.client else None
    rate_check = await check_chat_rate_limit(
        ip_address=client_ip,
        session_id=session_id,
        per_user_limit=per_user_limit,
    )
    if rate_check:
        raise RateLimitError()

    # Process through pipeline
    response = await chat_service.process_message(
        db=db,
        brand_id=brand.id,
        session_id=session_id,
        user_message=request.message,
        channel=request.channel,
    )

    return api_response(data=response)
