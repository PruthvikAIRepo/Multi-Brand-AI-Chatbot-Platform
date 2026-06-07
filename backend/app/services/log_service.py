from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.logs import (
    AdminActivityLog, ErrorLog, ComplianceLog, ModerationLog,
    RAGRetrievalLog, RecommendationRuleLog, APIUsageLog,
)
from app.models.enums import AdminActionType, ErrorType, ModerationReason, ApiUsageType


async def _paginated_query(db, model, filters, page, per_page, order_col):
    """Shared pagination helper for all log queries."""
    count_query = select(func.count()).select_from(model)
    data_query = select(model).order_by(order_col.desc())

    if filters:
        count_query = count_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        data_query.offset((page - 1) * per_page).limit(per_page)
    )
    return result.scalars().all(), total


async def list_admin_activity_logs(
    db: AsyncSession, page: int = 1, per_page: int = 20,
    brand_id: UUID | None = None, user_id: UUID | None = None,
    action_type: AdminActionType | None = None,
) -> tuple[list[dict], int]:
    filters = []
    if brand_id:
        filters.append(AdminActivityLog.brand_id == brand_id)
    if user_id:
        filters.append(AdminActivityLog.user_id == user_id)
    if action_type:
        filters.append(AdminActivityLog.action_type == action_type)

    logs, total = await _paginated_query(
        db, AdminActivityLog, filters, page, per_page, AdminActivityLog.created_at
    )
    return [_activity_to_dict(l) for l in logs], total


async def list_error_logs(
    db: AsyncSession, page: int = 1, per_page: int = 20,
    brand_id: UUID | None = None, error_type: ErrorType | None = None,
) -> tuple[list[dict], int]:
    filters = []
    if brand_id:
        filters.append(ErrorLog.brand_id == brand_id)
    if error_type:
        filters.append(ErrorLog.error_type == error_type)

    logs, total = await _paginated_query(
        db, ErrorLog, filters, page, per_page, ErrorLog.created_at
    )
    return [_error_to_dict(l) for l in logs], total


async def list_compliance_logs(
    db: AsyncSession, brand_id: UUID, page: int = 1, per_page: int = 20,
) -> tuple[list[dict], int]:
    logs, total = await _paginated_query(
        db, ComplianceLog, [ComplianceLog.brand_id == brand_id],
        page, per_page, ComplianceLog.created_at
    )
    return [_compliance_to_dict(l) for l in logs], total


async def list_moderation_logs(
    db: AsyncSession, brand_id: UUID, page: int = 1, per_page: int = 20,
    reason: ModerationReason | None = None,
) -> tuple[list[dict], int]:
    filters = [ModerationLog.brand_id == brand_id]
    if reason:
        filters.append(ModerationLog.reason == reason)

    logs, total = await _paginated_query(
        db, ModerationLog, filters, page, per_page, ModerationLog.created_at
    )
    return [_moderation_to_dict(l) for l in logs], total


async def list_rag_logs(
    db: AsyncSession, brand_id: UUID, page: int = 1, per_page: int = 20,
    below_threshold_only: bool = False,
) -> tuple[list[dict], int]:
    filters = [RAGRetrievalLog.brand_id == brand_id]
    if below_threshold_only:
        filters.append(RAGRetrievalLog.hit_threshold == False)

    logs, total = await _paginated_query(
        db, RAGRetrievalLog, filters, page, per_page, RAGRetrievalLog.created_at
    )
    return [_rag_to_dict(l) for l in logs], total


async def list_recommendation_rule_logs(
    db: AsyncSession, brand_id: UUID, page: int = 1, per_page: int = 20,
) -> tuple[list[dict], int]:
    logs, total = await _paginated_query(
        db, RecommendationRuleLog, [RecommendationRuleLog.brand_id == brand_id],
        page, per_page, RecommendationRuleLog.created_at
    )
    return [_rec_rule_to_dict(l) for l in logs], total


async def list_api_usage_logs(
    db: AsyncSession, page: int = 1, per_page: int = 20,
    brand_id: UUID | None = None, api_type: ApiUsageType | None = None,
) -> tuple[list[dict], int]:
    filters = []
    if brand_id:
        filters.append(APIUsageLog.brand_id == brand_id)
    if api_type:
        filters.append(APIUsageLog.api_type == api_type)

    logs, total = await _paginated_query(
        db, APIUsageLog, filters, page, per_page, APIUsageLog.created_at
    )
    return [_api_usage_to_dict(l) for l in logs], total


# --- Dict converters ---

def _activity_to_dict(l):
    return {
        "id": str(l.id), "user_id": str(l.user_id),
        "brand_id": str(l.brand_id) if l.brand_id else None,
        "action_type": l.action_type.value if l.action_type else None,
        "entity_type": l.entity_type, "entity_id": str(l.entity_id) if l.entity_id else None,
        "entity_name": l.entity_name, "ip_address": l.ip_address,
        "before_state": l.before_state, "after_state": l.after_state,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _error_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id) if l.brand_id else None,
        "channel": l.channel.value if l.channel else None,
        "error_type": l.error_type.value if l.error_type else None,
        "description": l.description,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _compliance_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id),
        "conversation_id": str(l.conversation_id) if l.conversation_id else None,
        "message_id": str(l.message_id) if l.message_id else None,
        "original_response": l.original_response, "replacement": l.replacement,
        "reason": l.reason,
        "rule_triggered_id": str(l.rule_triggered_id) if l.rule_triggered_id else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _moderation_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id),
        "conversation_id": str(l.conversation_id) if l.conversation_id else None,
        "user_identifier": l.user_identifier, "blocked_input": l.blocked_input,
        "reason": l.reason.value if l.reason else None,
        "action_taken": l.action_taken.value if l.action_taken else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _rag_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id),
        "conversation_id": str(l.conversation_id) if l.conversation_id else None,
        "user_query": l.user_query, "chunks_retrieved": l.chunks_retrieved,
        "chunks_retrieved_count": l.chunks_retrieved_count,
        "top_similarity_score": l.top_similarity_score,
        "hit_threshold": l.hit_threshold,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _rec_rule_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id),
        "conversation_id": str(l.conversation_id) if l.conversation_id else None,
        "user_input_summary": l.user_input_summary,
        "skin_type": l.skin_type.value if l.skin_type else None,
        "concerns": l.concerns, "matched_products": l.matched_products,
        "matched_count": l.matched_count, "excluded_products": l.excluded_products,
        "excluded_count": l.excluded_count, "applied_filters": l.applied_filters,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

def _api_usage_to_dict(l):
    return {
        "id": str(l.id), "brand_id": str(l.brand_id),
        "conversation_id": str(l.conversation_id) if l.conversation_id else None,
        "api_type": l.api_type.value if l.api_type else None,
        "tokens_in": l.tokens_in, "tokens_out": l.tokens_out,
        "chunks_count": l.chunks_count, "model": l.model,
        "latency_ms": l.latency_ms,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }
