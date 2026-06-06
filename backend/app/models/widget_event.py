from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin


class WidgetEvent(Base, UUIDMixin):
    __tablename__ = "widget_events"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    session_id = Column(String(255))
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default="now()", index=True)
