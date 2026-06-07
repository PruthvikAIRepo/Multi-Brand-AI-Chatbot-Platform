"""Post-processing compliance filter. Checks every AI response before delivery."""

import re
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.compliance_rule import ComplianceRule
from app.models.brand_config import BrandConfig


async def check_response(db: AsyncSession, brand_id: UUID, response_text: str) -> dict:
    """Check AI response against brand's compliance rules.
    Returns {is_clean, response, violations}."""

    # Load active blocked phrases
    result = await db.execute(
        select(ComplianceRule).where(
            ComplianceRule.brand_id == brand_id,
            ComplianceRule.is_active == True,
            ComplianceRule.rule_type.in_(["blocked_phrase", "blocked_topic"]),
        )
    )
    rules = result.scalars().all()

    violations = []

    for rule in rules:
        if rule.value.lower() in response_text.lower():
            violations.append({
                "rule_id": str(rule.id),
                "rule_type": rule.rule_type.value,
                "value": rule.value,
            })

    # Check for common medical claim patterns
    medical_patterns = [
        r'\b(cure|cures|curing)\b',
        r'\b(treat|treats|treating)\s+(acne|eczema|rosacea|psoriasis|dermatitis)',
        r'\b(diagnos|prescri)',
        r'\b(guaranteed|100%\s+effective)',
        r'\b(FDA\s+approved|clinically\s+proven)\b',
    ]

    for pattern in medical_patterns:
        if re.search(pattern, response_text, re.IGNORECASE):
            violations.append({
                "rule_id": None,
                "rule_type": "medical_claim_pattern",
                "value": pattern,
            })

    if violations:
        # Get fallback message
        config_result = await db.execute(
            select(BrandConfig).where(BrandConfig.brand_id == brand_id)
        )
        config = config_result.scalar_one_or_none()
        fallback = config.fallback_message if config else "I'm not sure about that. Please contact our support team."

        return {
            "is_clean": False,
            "response": fallback,
            "original_response": response_text,
            "violations": violations,
        }

    return {
        "is_clean": True,
        "response": response_text,
        "original_response": response_text,
        "violations": [],
    }
