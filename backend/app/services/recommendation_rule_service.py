from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.recommendation_rule import RecommendationRule
from app.models.product import Product, ProductSkinType, ProductConcern
from app.models.enums import RecommendationRuleType, SkinType, SkinConcern
from app.core.exceptions import NotFoundError


async def create_rule(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    rule = RecommendationRule(
        brand_id=brand_id,
        rule_type=data["rule_type"],
        config=data["config"],
        description=data.get("description"),
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
    rule_type: RecommendationRuleType | None = None,
    active_only: bool = False,
) -> tuple[list[dict], int]:
    base_filter = [RecommendationRule.brand_id == brand_id]

    if rule_type:
        base_filter.append(RecommendationRule.rule_type == rule_type)
    if active_only:
        base_filter.append(RecommendationRule.is_active == True)

    count_result = await db.execute(
        select(func.count()).select_from(RecommendationRule).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(RecommendationRule)
        .where(*base_filter)
        .order_by(RecommendationRule.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rules = result.scalars().all()

    return [_rule_to_dict(r) for r in rules], total


async def get_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID) -> dict:
    result = await db.execute(
        select(RecommendationRule).where(
            RecommendationRule.id == rule_id,
            RecommendationRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Recommendation rule", str(rule_id))
    return _rule_to_dict(rule)


async def update_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID, data: dict) -> dict:
    result = await db.execute(
        select(RecommendationRule).where(
            RecommendationRule.id == rule_id,
            RecommendationRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Recommendation rule", str(rule_id))

    for field in ["rule_type", "config", "description", "is_active"]:
        if field in data:
            setattr(rule, field, data[field])

    await db.flush()
    return _rule_to_dict(rule)


async def delete_rule(db: AsyncSession, brand_id: UUID, rule_id: UUID) -> None:
    result = await db.execute(
        select(RecommendationRule).where(
            RecommendationRule.id == rule_id,
            RecommendationRule.brand_id == brand_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Recommendation rule", str(rule_id))

    await db.delete(rule)
    await db.flush()


async def test_rules(
    db: AsyncSession,
    brand_id: UUID,
    skin_type: SkinType,
    concerns: list[SkinConcern],
    preferences: list[str],
) -> dict:
    """Simulate the recommendation rules engine against a test profile.
    Returns matched products, excluded products, and applied filters."""

    # 1. Get all active products for this brand that match the skin type
    product_query = (
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
            Product.is_in_stock == True,
        )
    )
    result = await db.execute(product_query)
    all_products = result.scalars().unique().all()

    # 2. Filter by skin type
    skin_matched = []
    for p in all_products:
        product_skin_types = {st.skin_type for st in p.skin_types}
        if skin_type in product_skin_types or not product_skin_types:
            skin_matched.append(p)

    # 3. Score by concern match
    scored = []
    for p in skin_matched:
        product_concerns = {c.concern for c in p.concerns}
        concern_match_count = len(product_concerns.intersection(set(concerns)))
        scored.append((p, concern_match_count + p.priority_score))

    # 4. Get all active rules
    rules_result = await db.execute(
        select(RecommendationRule).where(
            RecommendationRule.brand_id == brand_id,
            RecommendationRule.is_active == True,
        )
    )
    rules = rules_result.scalars().all()

    # 5. Apply exclusion and conflict rules
    excluded = []
    excluded_ids = set()

    for rule in rules:
        if rule.rule_type == RecommendationRuleType.EXCLUSION:
            product_id = rule.config.get("product_id")
            excluded_for_skin = rule.config.get("excluded_for_skin_types", [])
            excluded_for_concerns = rule.config.get("excluded_for_concerns", [])

            if skin_type.value in excluded_for_skin or any(c.value in excluded_for_concerns for c in concerns):
                excluded.append({
                    "product_id": product_id,
                    "reason": f"Exclusion rule: {rule.description or rule.config}",
                    "rule_id": str(rule.id),
                })
                excluded_ids.add(product_id)

        elif rule.rule_type == RecommendationRuleType.CONFLICT:
            # Conflict rules remove one product if both are present
            a_id = rule.config.get("product_a_id")
            b_id = rule.config.get("product_b_id")
            matched_ids = {str(p.id) for p, _ in scored}

            if a_id in matched_ids and b_id in matched_ids:
                # Remove the lower-priority one
                excluded.append({
                    "product_id": b_id,
                    "reason": f"Conflict rule: {rule.config.get('reason', 'Conflicting products')}",
                    "rule_id": str(rule.id),
                })
                excluded_ids.add(b_id)

    # 6. Final matched list (excluding excluded products)
    final = [
        (p, score) for p, score in scored
        if str(p.id) not in excluded_ids
    ]
    final.sort(key=lambda x: x[1], reverse=True)

    return {
        "input": {
            "skin_type": skin_type.value,
            "concerns": [c.value for c in concerns],
            "preferences": preferences,
        },
        "total_products": len(all_products),
        "skin_type_matched": len(skin_matched),
        "matched_products": [
            {
                "product_id": str(p.id),
                "product_name": p.name,
                "category": p.category,
                "price": str(p.price),
                "score": score,
                "skin_types": [st.skin_type.value for st in p.skin_types],
                "concerns": [c.concern.value for c in p.concerns],
            }
            for p, score in final
        ],
        "excluded_products": excluded,
        "rules_applied": len(rules),
    }


def _rule_to_dict(rule: RecommendationRule) -> dict:
    return {
        "id": str(rule.id),
        "brand_id": str(rule.brand_id),
        "rule_type": rule.rule_type.value,
        "config": rule.config,
        "description": rule.description,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }
