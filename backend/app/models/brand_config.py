from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ResponseLength, CaptureTrigger


class BrandConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brand_configs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Response settings
    response_length = Column(Enum(ResponseLength, name="response_length"), default=ResponseLength.MEDIUM)
    max_tokens = Column(Integer, default=1000)
    rag_similarity_threshold = Column(Float, default=0.7)
    recommendation_top_n = Column(Integer, default=3)
    session_timeout_minutes = Column(Integer, default=30)

    # Messages
    greeting_message = Column(Text)
    signoff_message = Column(Text)
    fallback_message = Column(Text, default="I am not sure about that. Please reach out to our support team.")
    fallback_tone_profile = Column(Text)

    # Conversation boundaries
    no_medical_claims = Column(Boolean, default=True)
    no_over_explaining = Column(Boolean, default=True)
    no_aggressive_upselling = Column(Boolean, default=True)
    no_unnecessary_details = Column(Boolean, default=True)
    no_medical_tone = Column(Boolean, default=True)

    # Rate limiting
    rate_limit_per_user = Column(Integer, default=30)

    # Data retention
    conversation_retention_days = Column(Integer, default=90)

    # Lead capture
    lead_capture_trigger = Column(Enum(CaptureTrigger, name="capture_trigger"), default=CaptureTrigger.AFTER_N_MESSAGES)
    lead_capture_n_messages = Column(Integer, default=3)
    lead_show_phone_field = Column(Boolean, default=False)
    lead_gdpr_consent_text = Column(Text, default="I agree to the collection and processing of my data.")
    lead_allow_skip = Column(Boolean, default=True)

    brand = relationship("Brand", back_populates="config")
