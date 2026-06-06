from sqlalchemy import Column, String, Text, Boolean, Enum, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin
from app.models.enums import NotificationType


class Notification(Base, UUIDMixin):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"))
    notification_type = Column(Enum(NotificationType, name="notification_type"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    action_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)
