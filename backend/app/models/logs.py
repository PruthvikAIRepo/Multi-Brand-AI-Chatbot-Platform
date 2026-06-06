from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin
from app.models.enums import (
    AdminActionType, ErrorType, ModerationReason, ModerationResponse,
    ChannelType, SkinType, ApiUsageType,
)


class AdminActivityLog(Base, UUIDMixin):
    __tablename__ = "admin_activity_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), index=True)
    action_type = Column(Enum(AdminActionType, name="admin_action_type"), nullable=False, index=True)
    entity_type = Column(String(100))
    entity_id = Column(UUID(as_uuid=True))
    entity_name = Column(String(255))
    ip_address = Column(String(45))
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class ErrorLog(Base, UUIDMixin):
    __tablename__ = "error_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), index=True)
    channel = Column(Enum(ChannelType, name="channel_type", create_constraint=False))
    error_type = Column(Enum(ErrorType, name="error_type"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class ComplianceLog(Base, UUIDMixin):
    __tablename__ = "compliance_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    original_response = Column(Text, nullable=False)
    replacement = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    rule_triggered_id = Column(UUID(as_uuid=True), ForeignKey("compliance_rules.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class ModerationLog(Base, UUIDMixin):
    __tablename__ = "moderation_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    user_identifier = Column(Text, index=True)
    blocked_input = Column(Text, nullable=False)
    reason = Column(Enum(ModerationReason, name="moderation_reason"), nullable=False, index=True)
    action_taken = Column(Enum(ModerationResponse, name="moderation_response", create_constraint=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class RAGRetrievalLog(Base, UUIDMixin):
    __tablename__ = "rag_retrieval_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    user_query = Column(Text, nullable=False)
    chunks_retrieved = Column(JSONB, server_default=text("'[]'::jsonb"))
    chunks_retrieved_count = Column(Integer, default=0)
    top_similarity_score = Column(Float)
    hit_threshold = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class RecommendationRuleLog(Base, UUIDMixin):
    __tablename__ = "recommendation_rule_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    user_input_summary = Column(Text)
    skin_type = Column(Enum(SkinType, name="skin_type", create_constraint=False))
    concerns = Column(JSONB, server_default=text("'[]'::jsonb"))
    matched_products = Column(JSONB, server_default=text("'[]'::jsonb"))
    matched_count = Column(Integer, default=0)
    excluded_products = Column(JSONB, server_default=text("'[]'::jsonb"))
    excluded_count = Column(Integer, default=0)
    applied_filters = Column(JSONB, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)


class APIUsageLog(Base, UUIDMixin):
    __tablename__ = "api_usage_logs"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))
    api_type = Column(Enum(ApiUsageType, name="api_usage_type"), nullable=False, index=True)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    chunks_count = Column(Integer)
    model = Column(String(100))
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), index=True)
