from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import log_service
from app.core.permissions import get_current_user, require_super_admin, check_brand_permission
from app.core.response import paginated_response
from app.models.user import User
from app.models.enums import AdminActionType, ErrorType, ModerationReason, ApiUsageType

router = APIRouter(tags=["Logs"])


# --- System-wide logs (Super Admin) ---

@router.get("/logs/admin-activity", response_model=dict)
async def list_admin_activity_logs(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None, user_id: UUID | None = None,
    action_type: AdminActionType | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin activity audit trail. Super Admin only."""
    data, total = await log_service.list_admin_activity_logs(
        db, page, per_page, brand_id, user_id, action_type
    )
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/logs/errors", response_model=dict)
async def list_error_logs(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None, error_type: ErrorType | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Error logs. Super Admin only."""
    data, total = await log_service.list_error_logs(db, page, per_page, brand_id, error_type)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/logs/api-usage", response_model=dict)
async def list_api_usage_logs(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    brand_id: UUID | None = None, api_type: ApiUsageType | None = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """API usage logs (Claude + Embeddings). Super Admin only."""
    data, total = await log_service.list_api_usage_logs(db, page, per_page, brand_id, api_type)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


# --- Brand-scoped logs ---

@router.get("/brands/{brand_id}/logs/compliance", response_model=dict)
async def list_compliance_logs(
    brand_id: UUID, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Compliance logs for a brand. Requires logs.view."""
    await check_brand_permission(db, current_user, brand_id, "logs.view")
    data, total = await log_service.list_compliance_logs(db, brand_id, page, per_page)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/brands/{brand_id}/logs/moderation", response_model=dict)
async def list_moderation_logs(
    brand_id: UUID, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    reason: ModerationReason | None = None,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Moderation logs for a brand. Requires logs.view."""
    await check_brand_permission(db, current_user, brand_id, "logs.view")
    data, total = await log_service.list_moderation_logs(db, brand_id, page, per_page, reason)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/brands/{brand_id}/logs/rag", response_model=dict)
async def list_rag_logs(
    brand_id: UUID, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    below_threshold_only: bool = False,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """RAG retrieval logs for a brand. Requires logs.view."""
    await check_brand_permission(db, current_user, brand_id, "logs.view")
    data, total = await log_service.list_rag_logs(db, brand_id, page, per_page, below_threshold_only)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/brands/{brand_id}/logs/recommendation-rules", response_model=dict)
async def list_recommendation_rule_logs(
    brand_id: UUID, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Recommendation rule execution logs. Requires logs.view."""
    await check_brand_permission(db, current_user, brand_id, "logs.view")
    data, total = await log_service.list_recommendation_rule_logs(db, brand_id, page, per_page)
    return paginated_response(data=data, total=total, page=page, per_page=per_page)
