"""Chat endpoint — the public-facing API that users interact with.
No admin auth required — this is for end users via the chat widget."""

import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import chat_service
from app.core.response import api_response
from app.models.enums import ChannelType

router = APIRouter(prefix="/chat", tags=["Chat (Public)"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None  # None = new session
    channel: ChannelType = ChannelType.WEBSITE


@router.post("/{brand_slug}", response_model=dict)
async def send_message(
    brand_slug: str,
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a brand's chatbot. Public endpoint — no auth needed.

    This is the main endpoint the chat widget calls.
    - brand_slug identifies which brand's chatbot to use
    - session_id tracks the conversation (auto-generated if not provided)
    - The full pipeline runs: moderation → RAG → LLM → compliance → response
    """
    from sqlalchemy import select
    from app.models.brand import Brand

    # Resolve brand by slug
    result = await db.execute(select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True))
    brand = result.scalar_one_or_none()
    if not brand:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Brand", brand_slug)

    # Generate session_id if not provided
    session_id = request.session_id or f"web_{uuid.uuid4().hex[:16]}"

    # Process through the full pipeline
    response = await chat_service.process_message(
        db=db,
        brand_id=brand.id,
        session_id=session_id,
        user_message=request.message,
        channel=request.channel,
    )

    return api_response(data=response)
