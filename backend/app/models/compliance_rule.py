from sqlalchemy import Column, Text, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ComplianceRuleType


class ComplianceRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_rules"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(Enum(ComplianceRuleType, name="compliance_rule_type"), nullable=False, index=True)
    value = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    brand = relationship("Brand", back_populates="compliance_rules")
