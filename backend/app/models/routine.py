from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import SkinType, RoutineStepName


class Routine(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "routines"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_skin_type = Column(Enum(SkinType, name="skin_type", create_constraint=False))
    target_concerns = Column(JSONB, default=[])
    is_active = Column(Boolean, default=True, index=True)
    deleted_at = Column(DateTime(timezone=True))

    brand = relationship("Brand", back_populates="routines")
    steps = relationship("RoutineStep", back_populates="routine", cascade="all, delete-orphan", order_by="RoutineStep.step_number")


class RoutineStep(Base, UUIDMixin):
    __tablename__ = "routine_steps"

    routine_id = Column(UUID(as_uuid=True), ForeignKey("routines.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    step_name = Column(Enum(RoutineStepName, name="routine_step_name"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    instructions = Column(Text)

    __table_args__ = (UniqueConstraint("routine_id", "step_number"),)

    routine = relationship("Routine", back_populates="steps")
    product = relationship("Product")
