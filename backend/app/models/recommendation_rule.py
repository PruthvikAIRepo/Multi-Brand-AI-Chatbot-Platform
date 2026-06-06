from sqlalchemy import Column, Text, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import RecommendationRuleType


class RecommendationRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recommendation_rules"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(Enum(RecommendationRuleType, name="recommendation_rule_type"), nullable=False, index=True)
    config = Column(JSONB, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    brand = relationship("Brand", back_populates="recommendation_rules")
