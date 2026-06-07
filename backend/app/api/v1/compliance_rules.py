from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.compliance_rule import ComplianceRuleCreateRequest, ComplianceRuleUpdateRequest
from app.services import compliance_rule_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import ComplianceRuleType

router = APIRouter(prefix="/brands/{brand_id}/compliance-rules", tags=["Compliance Rules"])


@router.post("", response_model=dict)
async def create_rule(
    brand_id: UUID,
    request: ComplianceRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a compliance rule. Requires compliance.edit."""
    await check_brand_permission(db, current_user, brand_id, "compliance.edit")
    rule = await compliance_rule_service.create_rule(db, brand_id, request.model_dump())
    return api_response(data=rule, message="Compliance rule created")


@router.get("", response_model=dict)
async def list_rules(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    rule_type: ComplianceRuleType | None = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List compliance rules with filters. Requires compliance.view."""
    await check_brand_permission(db, current_user, brand_id, "compliance.view")
    rules, total = await compliance_rule_service.list_rules(
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
    """Get a single compliance rule. Requires compliance.view."""
    await check_brand_permission(db, current_user, brand_id, "compliance.view")
    rule = await compliance_rule_service.get_rule(db, brand_id, rule_id)
    return api_response(data=rule)


@router.put("/{rule_id}", response_model=dict)
async def update_rule(
    brand_id: UUID,
    rule_id: UUID,
    request: ComplianceRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a compliance rule. Requires compliance.edit."""
    await check_brand_permission(db, current_user, brand_id, "compliance.edit")
    rule = await compliance_rule_service.update_rule(
        db, brand_id, rule_id, request.model_dump(exclude_unset=True)
    )
    return api_response(data=rule, message="Compliance rule updated")


@router.delete("/{rule_id}", response_model=dict)
async def delete_rule(
    brand_id: UUID,
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a compliance rule (hard delete). Requires compliance.edit."""
    await check_brand_permission(db, current_user, brand_id, "compliance.edit")
    await compliance_rule_service.delete_rule(db, brand_id, rule_id)
    return api_response(message="Compliance rule deleted")
