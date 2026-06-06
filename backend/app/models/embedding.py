from sqlalchemy import Column, Text, Float, Boolean, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import EntityType, EmbeddingStatus


class EmbeddingSyncStatus(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "embedding_sync_status"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(Enum(EntityType, name="entity_type"), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(EmbeddingStatus, name="embedding_status"), default=EmbeddingStatus.PENDING, index=True)
    error_message = Column(Text)

    __table_args__ = (UniqueConstraint("entity_type", "entity_id"),)


class Embedding(Base, UUIDMixin):
    __tablename__ = "embeddings"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(Enum(EntityType, name="entity_type", create_constraint=False), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
