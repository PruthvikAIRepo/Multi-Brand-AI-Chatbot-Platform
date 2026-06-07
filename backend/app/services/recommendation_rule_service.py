from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.recommendation_rule import RecommendationRule
from app.models.product import Product, ProductSkinType, ProductConcern
from app.models.brand_config import BrandConfig
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
    """Simulate the recommendation rules engine.
    SRS Section 24.2: Rules engine filters → Priority sort → Top N → AI presents.
    This endpoint shows the rules engine output (before AI presentation)."""

    # Get brand config for top_n
    config_result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand_id))
    brand_config = config_result.scalar_one_or_none()
    top_n = brand_config.recommendation_top_n if brand_config else 3

    # Step 1: Get all in-stock, non-deleted products
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
            Product.is_in_stock == True,
        )
    )
    all_products = result.scalars().unique().all()

    if not all_products:
        return _fallback_response(skin_type, concerns, preferences, "no_products",
                                  "No products available for this brand")

    # Step 2: Filter by skin type
    skin_matched = []
    for p in all_products:
        product_skin_types = {st.skin_type for st in p.skin_types}
        if not product_skin_types or skin_type in product_skin_types:
            skin_matched.append(p)

    if not skin_matched:
        return _fallback_response(skin_type, concerns, preferences, "no_skin_match",
                                  "No products match the given skin type")

    # Step 3: Base scoring — concern match + product priority_score
    product_scores: dict[UUID, float] = {}
    for p in skin_matched:
        product_concerns = {c.concern for c in p.concerns}
        concern_match = len(product_concerns.intersection(set(concerns)))
        product_scores[p.id] = concern_match + p.priority_score

    # Step 4: Get all active rules
    rules_result = await db.execute(
        select(RecommendationRule).where(
            RecommendationRule.brand_id == brand_id,
            RecommendationRule.is_active == True,
        )
    )
    rules = rules_result.scalars().all()

    # Step 5: Apply priority rules (override/boost scores)
    for rule in rules:
        if rule.rule_type == RecommendationRuleType.PRIORITY:
            pid = rule.config.get("product_id")
            boost = rule.config.get("priority_score", 0)
            if pid and UUID(pid) in product_scores:
                product_scores[UUID(pid)] += boost

    # Step 6: Apply suitability matrix rules (multi-axis scoring)
    for rule in rules:
        if rule.rule_type == RecommendationRuleType.SUITABILITY:
            pid = rule.config.get("product_id")
            if not pid or UUID(pid) not in product_scores:
                continue
            skin_scores = rule.config.get("skin_type_scores", {})
            concern_scores = rule.config.get("concern_scores", {})
            # Add skin type suitability score
            product_scores[UUID(pid)] += skin_scores.get(skin_type.value, 0)
            # Add concern suitability scores
            for c in concerns:
                product_scores[UUID(pid)] += concern_scores.get(c.value, 0)

    # Step 7: Apply exclusion rules
    excluded = []
    excluded_ids = set()

    for rule in rules:
        if rule.rule_type == RecommendationRuleType.EXCLUSION:
            pid = rule.config.get("product_id")
            if not pid or UUID(pid) not in product_scores:
                continue
            excluded_for_skin = rule.config.get("excluded_for_skin_types", [])
            excluded_for_concerns = rule.config.get("excluded_for_concerns", [])

            should_exclude = (
                skin_type.value in excluded_for_skin
                or any(c.value in excluded_for_concerns for c in concerns)
            )
            if should_exclude:
                excluded.append({
                    "product_id": pid,
                    "reason": f"Exclusion rule: {rule.description or 'Excluded for this profile'}",
                    "rule_id": str(rule.id),
                })
                excluded_ids.add(UUID(pid))

    # Step 8: Apply conflict rules (remove the LOWER-scored product)
    for rule in rules:
        if rule.rule_type == RecommendationRuleType.CONFLICT:
            a_id = rule.config.get("product_a_id")
            b_id = rule.config.get("product_b_id")
            if not a_id or not b_id:
                continue

            a_uuid = UUID(a_id)
            b_uuid = UUID(b_id)

            a_in = a_uuid in product_scores and a_uuid not in excluded_ids
            b_in = b_uuid in product_scores and b_uuid not in excluded_ids

            if a_in and b_in:
                # Remove the lower-scored product
                if product_scores.get(a_uuid, 0) >= product_scores.get(b_uuid, 0):
                    remove_id, remove_uuid = b_id, b_uuid
                else:
                    remove_id, remove_uuid = a_id, a_uuid

                excluded.append({
                    "product_id": remove_id,
                    "reason": f"Conflict rule: {rule.config.get('reason', 'Conflicting products')}",
                    "rule_id": str(rule.id),
                })
                excluded_ids.add(remove_uuid)

    # Step 9: Build final ranked list (exclude removed, sort by score, limit to top_n)
    product_map = {p.id: p for p in skin_matched}
    final = [
        (product_map[pid], score)
        for pid, score in product_scores.items()
        if pid not in excluded_ids and pid in product_map
    ]
    final.sort(key=lambda x: x[1], reverse=True)
    final = final[:top_n]

    if not final:
        return _fallback_response(skin_type, concerns, preferences, "all_excluded",
                                  "All matching products were excluded by rules. Consider reviewing your recommendation rules.")

    return {
        "input": {
            "skin_type": skin_type.value,
            "concerns": [c.value for c in concerns],
            "preferences": preferences,
        },
        "fallback": None,
        "total_products": len(all_products),
        "skin_type_matched": len(skin_matched),
        "top_n": top_n,
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


def _fallback_response(
    skin_type: SkinType, concerns: list, preferences: list, fallback_type: str, message: str
) -> dict:
    return {
        "input": {
            "skin_type": skin_type.value,
            "concerns": [c.value for c in concerns],
            "preferences": preferences,
        },
        "fallback": {"type": fallback_type, "message": message},
        "total_products": 0,
        "skin_type_matched": 0,
        "top_n": 0,
        "matched_products": [],
        "excluded_products": [],
        "rules_applied": 0,
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
