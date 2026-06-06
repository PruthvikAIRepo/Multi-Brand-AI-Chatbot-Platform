from sqlalchemy import Column, Boolean, Enum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import EmotionalStyle, CommunicationStyle, SoftnessLevel


class ToneSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tone_settings"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Core tone
    emotional_style = Column(Enum(EmotionalStyle, name="emotional_style"), default=EmotionalStyle.WARM)
    communication_style = Column(Enum(CommunicationStyle, name="communication_style"), default=CommunicationStyle.CASUAL)
    emoji_usage = Column(Boolean, default=False)
    vocabulary_preferred = Column(JSONB, server_default=text("'[]'::jsonb"))
    vocabulary_avoided = Column(JSONB, server_default=text("'[]'::jsonb"))

    # Micro-tone rules
    softness_level = Column(Enum(SoftnessLevel, name="softness_level"), default=SoftnessLevel.GENTLE)
    sensory_language_enabled = Column(Boolean, default=True)
    emotional_cues = Column(JSONB, server_default=text("'[]'::jsonb"))
    restricted_adjectives = Column(JSONB, server_default=text("'[]'::jsonb"))
    clinical_language_allowed = Column(Boolean, default=False)
    harsh_word_blocking = Column(Boolean, default=True)

    brand = relationship("Brand", back_populates="tone_setting")
