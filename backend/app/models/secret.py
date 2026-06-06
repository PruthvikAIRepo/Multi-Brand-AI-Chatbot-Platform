from sqlalchemy import Column, String, LargeBinary, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import SecretType


class Secret(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "secrets"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), index=True)  # NULL = system default
    secret_type = Column(Enum(SecretType, name="secret_type"), nullable=False, index=True)
    encrypted_value = Column(LargeBinary, nullable=False)
    last_four_chars = Column(String(4))

    __table_args__ = (UniqueConstraint("brand_id", "secret_type", name="uq_secrets_brand_type"),)
