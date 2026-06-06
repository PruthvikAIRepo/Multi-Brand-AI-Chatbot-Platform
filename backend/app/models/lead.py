from sqlalchemy import Column, String, Text, Boolean, LargeBinary, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ChannelType


class Lead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leads"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email_encrypted = Column(LargeBinary, nullable=False)
    email_hash = Column(String(64), nullable=False, index=True)
    phone_encrypted = Column(LargeBinary)
    channel = Column(Enum(ChannelType, name="channel_type", create_constraint=False), nullable=False, index=True)
    consent = Column(Boolean, nullable=False, default=False)
    consent_text = Column(Text)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))

    __table_args__ = (UniqueConstraint("brand_id", "email_hash", name="uq_leads_brand_email"),)

    brand = relationship("Brand", back_populates="leads")
    conversation = relationship("Conversation")
