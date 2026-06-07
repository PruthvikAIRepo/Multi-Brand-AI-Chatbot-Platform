from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.conversation import Conversation, Message
from app.models.enums import ChannelType
from app.core.exceptions import NotFoundError


async def list_conversations(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    channel: ChannelType | None = None,
    flagged_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [Conversation.brand_id == brand_id]

    if channel:
        base_filter.append(Conversation.channel == channel)
    if flagged_only:
        base_filter.append(Conversation.is_flagged == True)

    count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Conversation)
        .where(*base_filter)
        .order_by(Conversation.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    conversations = result.scalars().all()

    # Get message counts per conversation in batch
    conv_ids = [c.id for c in conversations]
    msg_counts = {}
    if conv_ids:
        mc_result = await db.execute(
            select(Message.conversation_id, func.count(Message.id))
            .where(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
        )
        msg_counts = {row[0]: row[1] for row in mc_result.all()}

    data = [_conversation_list_dict(c, msg_counts.get(c.id, 0)) for c in conversations]
    return data, total


async def get_conversation(db: AsyncSession, brand_id: UUID, conversation_id: UUID) -> dict:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.brand_id == brand_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation", str(conversation_id))

    return _conversation_detail_dict(conversation)


async def flag_conversation(
    db: AsyncSession, brand_id: UUID, conversation_id: UUID, reason: str | None
) -> dict:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.brand_id == brand_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation", str(conversation_id))

    conversation.is_flagged = True
    conversation.flag_reason = reason
    await db.flush()
    return {"id": str(conversation.id), "is_flagged": True, "flag_reason": reason}


async def unflag_conversation(db: AsyncSession, brand_id: UUID, conversation_id: UUID) -> dict:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.brand_id == brand_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation", str(conversation_id))

    conversation.is_flagged = False
    conversation.flag_reason = None
    await db.flush()
    return {"id": str(conversation.id), "is_flagged": False}


async def delete_conversation(db: AsyncSession, brand_id: UUID, conversation_id: UUID) -> None:
    """GDPR: Hard delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.brand_id == brand_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation", str(conversation_id))

    await db.delete(conversation)
    await db.flush()


def _conversation_list_dict(c: Conversation, message_count: int) -> dict:
    return {
        "id": str(c.id),
        "session_id": c.session_id,
        "channel": c.channel.value if c.channel else None,
        "user_identifier": c.user_identifier,
        "is_flagged": c.is_flagged,
        "flag_reason": c.flag_reason,
        "current_handler": c.current_handler.value if c.current_handler else "ai",
        "is_escalated": c.is_escalated,
        "message_count": message_count,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "ended_at": c.ended_at.isoformat() if c.ended_at else None,
    }


def _conversation_detail_dict(c: Conversation) -> dict:
    return {
        "id": str(c.id),
        "brand_id": str(c.brand_id),
        "session_id": c.session_id,
        "channel": c.channel.value if c.channel else None,
        "user_identifier": c.user_identifier,
        "session_state": c.session_state or {},
        "is_flagged": c.is_flagged,
        "flag_reason": c.flag_reason,
        "current_handler": c.current_handler.value if c.current_handler else "ai",
        "is_escalated": c.is_escalated,
        "escalation_reason": c.escalation_reason,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "ended_at": c.ended_at.isoformat() if c.ended_at else None,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in sorted(c.messages, key=lambda x: x.created_at)
        ],
    }
