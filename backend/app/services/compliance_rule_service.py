from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.compliance_rule import ComplianceRule
from app.models.enums import ComplianceRuleType
from app.core.exceptions import NotFoundError


async def create_rule(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    rule = ComplianceRule(
        brand_id=brand_id,
        rule_type=data["rule_type"],
        value=data["value"],
        is_active=data.get("is_active", True),
    )
    db.add(rule)
    await db.flush()
    return _rule_to_dict(rule)


async def list_rules(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    rule_type: ComplianceRuleType | None = None,
    active_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [ComplianceRule.brand_id == brand_id]

    if rule_type:
        base_filter.append(ComplianceRule.rule_type == rule_type)
    if active_only:
        base_filter.append(ComplianceRule.is_active == True)

    count_result = await db.execute(
        select(func.count()).select_from(ComplianceRule).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(ComplianceRule)
        .where(*base_filter)
        .order_by(ComplianceRule.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rules = result.scalars().all()

    return [_rule_to_dict(r) for r in rules], total


async def get_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID) -> dict:
    result = await db.execute(
        select(ComplianceRule).where(
            ComplianceRule.id == rule_id,
            ComplianceRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Compliance rule", str(rule_id))
    return _rule_to_dict(rule)


async def update_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID, data: dict) -> dict:
    result = await db.execute(
        select(ComplianceRule).where(
            ComplianceRule.id == rule_id,
            ComplianceRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Compliance rule", str(rule_id))

    for field in ["rule_type", "value", "is_active"]:
        if field in data:
            setattr(rule, field, data[field])

    await db.flush()
    return _rule_to_dict(rule)


async def delete_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID) -> None:
    result = await db.execute(
        select(ComplianceRule).where(
            ComplianceRule.id == rule_id,
            ComplianceRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Compliance rule", str(rule_id))

    await db.delete(rule)
    await db.flush()


def _rule_to_dict(rule: ComplianceRule) -> dict:
    return {
        "id": str(rule.id),
        "brand_id": str(rule.brand_id),
        "rule_type": rule.rule_type.value,
        "value": rule.value,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }
