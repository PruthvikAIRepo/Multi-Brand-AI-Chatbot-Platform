from sqlalchemy import Column, String, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ChatbotStatus


class Brand(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brands"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    logo_url = Column(Text)
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    accent_color = Column(String(7))
    description = Column(Text)
    currency = Column(String(3), default="INR")
    chatbot_status = Column(Enum(ChatbotStatus, name="chatbot_status"), default=ChatbotStatus.NORMAL)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    config = relationship("BrandConfig", back_populates="brand", uselist=False, cascade="all, delete-orphan")
    tone_setting = relationship("ToneSetting", back_populates="brand", uselist=False, cascade="all, delete-orphan")
    image_style = relationship("BrandImageStyle", back_populates="brand", uselist=False, cascade="all, delete-orphan")
    moderation_config = relationship("ModerationConfig", back_populates="brand", uselist=False, cascade="all, delete-orphan")
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="brand", cascade="all, delete-orphan")
    routines = relationship("Routine", back_populates="brand", cascade="all, delete-orphan")
    compliance_rules = relationship("ComplianceRule", back_populates="brand", cascade="all, delete-orphan")
    recommendation_rules = relationship("RecommendationRule", back_populates="brand", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="brand", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="brand", cascade="all, delete-orphan")
    prompt_versions = relationship("PromptVersion", back_populates="brand", cascade="all, delete-orphan")
