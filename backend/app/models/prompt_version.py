from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin


class PromptVersion(Base, UUIDMixin):
    __tablename__ = "prompt_versions"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    annotation = Column(Text)
    is_live = Column(Boolean, default=False, index=True)
    is_draft = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (UniqueConstraint("brand_id", "version_number"),)

    brand = relationship("Brand", back_populates="prompt_versions")
    creator = relationship("User")
