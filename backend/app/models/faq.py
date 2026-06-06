from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin


class FAQ(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "faqs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    deleted_at = Column(DateTime(timezone=True))

    brand = relationship("Brand", back_populates="faqs")
