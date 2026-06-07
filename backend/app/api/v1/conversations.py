from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import conversation_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import ChannelType


class FlagRequest(BaseModel):
    reason: str | None = None


router = APIRouter(prefix="/brands/{brand_id}/conversations", tags=["Conversations"])


@router.get("", response_model=dict)
async def list_conversations(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: ChannelType | None = None,
    flagged_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for a brand. Requires conversations.view."""
    await check_brand_permission(db, current_user, brand_id, "conversations.view")
    data, total = await conversation_service.list_conversations(
        db, brand_id, page, per_page, channel, flagged_only
    )
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    brand_id: UUID,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full conversation with messages. Requires conversations.view."""
    await check_brand_permission(db, current_user, brand_id, "conversations.view")
    data = await conversation_service.get_conversation(db, brand_id, conversation_id)
    return api_response(data=data)


@router.post("/{conversation_id}/flag", response_model=dict)
async def flag_conversation(
    brand_id: UUID,
    conversation_id: UUID,
    request: FlagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Flag a conversation for review. Requires conversations.view."""
    await check_brand_permission(db, current_user, brand_id, "conversations.view")
    data = await conversation_service.flag_conversation(db, brand_id, conversation_id, request.reason)
    return api_response(data=data, message="Conversation flagged")


@router.post("/{conversation_id}/unflag", response_model=dict)
async def unflag_conversation(
    brand_id: UUID,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove flag from conversation. Requires conversations.view."""
    await check_brand_permission(db, current_user, brand_id, "conversations.view")
    data = await conversation_service.unflag_conversation(db, brand_id, conversation_id)
    return api_response(data=data, message="Conversation unflagged")


@router.delete("/{conversation_id}", response_model=dict)
async def delete_conversation(
    brand_id: UUID,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR: Permanently delete a conversation and all its messages. Requires leads.delete."""
    await check_brand_permission(db, current_user, brand_id, "leads.delete")
    await conversation_service.delete_conversation(db, brand_id, conversation_id)
    return api_response(message="Conversation deleted permanently")
