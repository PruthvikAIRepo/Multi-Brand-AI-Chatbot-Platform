from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.logs import (
    AdminActivityLog, ErrorLog, ComplianceLog, ModerationLog,
    RAGRetrievalLog, RecommendationRuleLog, APIUsageLog,
)
from app.models.enums import AdminActionType, ErrorType, ModerationReason


async def list_admin_activity_logs(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    brand_id: UUID | None = None,
    user_id: UUID | None = None,
    action_type: AdminActionType | None = None,
) -> tuple[list[dict], int]:
    base_filter = []
    if brand_id:
        base_filter.append(AdminActivityLog.brand_id == brand_id)
    if user_id:
        base_filter.append(AdminActivityLog.user_id == user_id)
    if action_type:
        base_filter.append(AdminActivityLog.action_type == action_type)

    where_clause = AdminActivityLog.id.is_not(None)  # always-true base
    if base_filter:
        where_clause = *base_filter,

    count_result = await db.execute(
        select(func.count()).select_from(AdminActivityLog).where(*base_filter) if base_filter
        else select(func.count()).select_from(AdminActivityLog)
    )
    total = count_result.scalar()

    query = select(AdminActivityLog).order_by(AdminActivityLog.created_at.desc())
    if base_filter:
        query = query.where(*base_filter)
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [_activity_to_dict(l) for l in logs], total


async def list_error_logs(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    brand_id: UUID | None = None,
    error_type: ErrorType | None = None,
) -> tuple[list[dict], int]:
    base_filter = []
    if brand_id:
        base_filter.append(ErrorLog.brand_id == brand_id)
    if error_type:
        base_filter.append(ErrorLog.error_type == error_type)

    count_result = await db.execute(
        select(func.count()).select_from(ErrorLog).where(*base_filter) if base_filter
        else select(func.count()).select_from(ErrorLog)
    )
    total = count_result.scalar()

    query = select(ErrorLog).order_by(ErrorLog.created_at.desc())
    if base_filter:
        query = query.where(*base_filter)
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [_error_to_dict(l) for l in logs], total


async def list_compliance_logs(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    count_result = await db.execute(
        select(func.count()).select_from(ComplianceLog).where(ComplianceLog.brand_id == brand_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(ComplianceLog)
        .where(ComplianceLog.brand_id == brand_id)
        .order_by(ComplianceLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return [_compliance_to_dict(l) for l in logs], total


async def list_moderation_logs(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    reason: ModerationReason | None = None,
) -> tuple[list[dict], int]:
    base_filter = [ModerationLog.brand_id == brand_id]
    if reason:
        base_filter.append(ModerationLog.reason == reason)

    count_result = await db.execute(
        select(func.count()).select_from(ModerationLog).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(ModerationLog)
        .where(*base_filter)
        .order_by(ModerationLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return [_moderation_to_dict(l) for l in logs], total


async def list_rag_logs(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    below_threshold_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [RAGRetrievalLog.brand_id == brand_id]
    if below_threshold_only:
        base_filter.append(RAGRetrievalLog.hit_threshold == False)

    count_result = await db.execute(
        select(func.count()).select_from(RAGRetrievalLog).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(RAGRetrievalLog)
        .where(*base_filter)
        .order_by(RAGRetrievalLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return [_rag_to_dict(l) for l in logs], total


# --- Dict converters ---

def _activity_to_dict(log: AdminActivityLog) -> dict:
    return {
        "id": str(log.id),
        "user_id": str(log.user_id),
        "brand_id": str(log.brand_id) if log.brand_id else None,
        "action_type": log.action_type.value if log.action_type else None,
        "entity_type": log.entity_type,
        "entity_id": str(log.entity_id) if log.entity_id else None,
        "entity_name": log.entity_name,
        "ip_address": log.ip_address,
        "before_state": log.before_state,
        "after_state": log.after_state,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _error_to_dict(log: ErrorLog) -> dict:
    return {
        "id": str(log.id),
        "brand_id": str(log.brand_id) if log.brand_id else None,
        "channel": log.channel.value if log.channel else None,
        "error_type": log.error_type.value if log.error_type else None,
        "description": log.description,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _compliance_to_dict(log: ComplianceLog) -> dict:
    return {
        "id": str(log.id),
        "brand_id": str(log.brand_id),
        "conversation_id": str(log.conversation_id) if log.conversation_id else None,
        "message_id": str(log.message_id) if log.message_id else None,
        "original_response": log.original_response,
        "replacement": log.replacement,
        "reason": log.reason,
        "rule_triggered_id": str(log.rule_triggered_id) if log.rule_triggered_id else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _moderation_to_dict(log: ModerationLog) -> dict:
    return {
        "id": str(log.id),
        "brand_id": str(log.brand_id),
        "conversation_id": str(log.conversation_id) if log.conversation_id else None,
        "user_identifier": log.user_identifier,
        "blocked_input": log.blocked_input,
        "reason": log.reason.value if log.reason else None,
        "action_taken": log.action_taken.value if log.action_taken else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _rag_to_dict(log: RAGRetrievalLog) -> dict:
    return {
        "id": str(log.id),
        "brand_id": str(log.brand_id),
        "conversation_id": str(log.conversation_id) if log.conversation_id else None,
        "user_query": log.user_query,
        "chunks_retrieved": log.chunks_retrieved,
        "chunks_retrieved_count": log.chunks_retrieved_count,
        "top_similarity_score": log.top_similarity_score,
        "hit_threshold": log.hit_threshold,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
