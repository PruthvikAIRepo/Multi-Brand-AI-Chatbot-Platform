from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin


class IPBlockList(Base, UUIDMixin):
    __tablename__ = "ip_block_list"

    ip_address = Column(String(45), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    blocked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (UniqueConstraint("ip_address", "brand_id"),)


class UserBlockList(Base, UUIDMixin):
    __tablename__ = "user_block_list"

    user_identifier = Column(Text, nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    blocked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (UniqueConstraint("user_identifier", "brand_id"),)
