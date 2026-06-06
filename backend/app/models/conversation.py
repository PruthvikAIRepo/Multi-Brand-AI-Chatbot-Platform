from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ChannelType, MessageRole, ConversationHandler, EscalationStatus


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    channel = Column(Enum(ChannelType, name="channel_type"), nullable=False, index=True)
    user_identifier = Column(Text)
    session_state = Column(JSONB, server_default=text("'{}'::jsonb"))
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reason = Column(Text)

    # Human escalation
    current_handler = Column(Enum(ConversationHandler, name="conversation_handler"), default=ConversationHandler.AI)
    is_escalated = Column(Boolean, default=False)
    escalation_status = Column(Enum(EscalationStatus, name="escalation_status"))
    escalation_reason = Column(Text)
    escalated_at = Column(DateTime(timezone=True))
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    started_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)
    ended_at = Column(DateTime(timezone=True))

    brand = relationship("Brand", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])


class Message(Base, UUIDMixin):
    __tablename__ = "messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole, name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)

    conversation = relationship("Conversation", back_populates="messages")
