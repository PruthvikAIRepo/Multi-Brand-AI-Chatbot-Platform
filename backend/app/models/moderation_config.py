from sqlalchemy import Column, Enum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ModerationSensitivity, ModerationResponse


class ModerationConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "moderation_configs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True)

    sensitivity = Column(Enum(ModerationSensitivity, name="moderation_sensitivity"), default=ModerationSensitivity.MEDIUM)
    response_on_block = Column(Enum(ModerationResponse, name="moderation_response"), default=ModerationResponse.BRAND_FALLBACK)
    allow_list = Column(JSONB, server_default=text("'[]'::jsonb"))
    block_list = Column(JSONB, server_default=text("'[]'::jsonb"))
    prompt_injection_patterns = Column(JSONB, server_default=text("'[]'::jsonb"))

    brand = relationship("Brand", back_populates="moderation_config")
