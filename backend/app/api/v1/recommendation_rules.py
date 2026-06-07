from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.recommendation_rule import (
    RecommendationRuleCreateRequest, RecommendationRuleUpdateRequest, RuleTestRequest,
)
from app.services import recommendation_rule_service, audit_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import RecommendationRuleType, AdminActionType

router = APIRouter(prefix="/brands/{brand_id}/recommendation-rules", tags=["Recommendation Rules"])


@router.post("", response_model=dict)
async def create_rule(
    brand_id: UUID,
    request: RecommendationRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a recommendation rule. Requires recommendations.edit."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.edit")
    rule = await recommendation_rule_service.create_rule(db, brand_id, request.model_dump())
    await audit_service.log_action(
        db, current_user.id, AdminActionType.CREATED, "recommendation_rule",
        entity_id=rule.get("id"), brand_id=brand_id, entity_name=rule.get("name"),
    )
    return api_response(data=rule, message="Recommendation rule created")


@router.get("", response_model=dict)
async def list_rules(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    rule_type: RecommendationRuleType | None = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recommendation rules. Requires recommendations.view."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.view")
    rules, total = await recommendation_rule_service.list_rules(
        db, brand_id, page, per_page, rule_type, active_only
    )
    return paginated_response(data=rules, total=total, page=page, per_page=per_page)


@router.get("/{rule_id}", response_model=dict)
async def get_rule(
    brand_id: UUID,
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single recommendation rule. Requires recommendations.view."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.view")
    rule = await recommendation_rule_service.get_rule(db, brand_id, rule_id)
    return api_response(data=rule)


@router.put("/{rule_id}", response_model=dict)
async def update_rule(
    brand_id: UUID,
    rule_id: UUID,
    request: RecommendationRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a recommendation rule. Requires recommendations.edit."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.edit")
    rule = await recommendation_rule_service.update_rule(
        db, brand_id, rule_id, request.model_dump(exclude_unset=True)
    )
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "recommendation_rule",
        entity_id=rule_id, brand_id=brand_id, entity_name=rule.get("name"),
    )
    return api_response(data=rule, message="Recommendation rule updated")


@router.delete("/{rule_id}", response_model=dict)
async def delete_rule(
    brand_id: UUID,
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recommendation rule (hard delete). Requires recommendations.edit."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.edit")
    await recommendation_rule_service.delete_rule(db, brand_id, rule_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.DELETED, "recommendation_rule",
        entity_id=rule_id, brand_id=brand_id,
    )
    return api_response(message="Recommendation rule deleted")


@router.post("/test", response_model=dict)
async def test_rules(
    brand_id: UUID,
    request: RuleTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test recommendation rules against a simulated user profile.
    Shows which products would be recommended, excluded, and why.
    Requires recommendations.view."""
    await check_brand_permission(db, current_user, brand_id, "recommendations.view")
    result = await recommendation_rule_service.test_rules(
        db, brand_id, request.skin_type, request.concerns, request.preferences
    )
    return api_response(data=result)
