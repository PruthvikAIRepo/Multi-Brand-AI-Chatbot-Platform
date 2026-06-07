"""Post-processing compliance filter. Checks every AI response before delivery.
Supports blocked_phrase, blocked_topic, allowed_phrase (whitelist), and medical patterns."""

import re
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.compliance_rule import ComplianceRule
from app.models.brand_config import BrandConfig
from app.models.enums import ComplianceRuleType


async def check_response(db: AsyncSession, brand_id: UUID, response_text: str) -> dict:
    """Check AI response against brand's compliance rules.
    Returns {is_clean, response, original_response, violations}."""

    # Load all active compliance rules
    result = await db.execute(
        select(ComplianceRule).where(
            ComplianceRule.brand_id == brand_id,
            ComplianceRule.is_active == True,
        )
    )
    rules = result.scalars().all()

    # Separate rule types
    blocked_phrases = [r for r in rules if r.rule_type == ComplianceRuleType.BLOCKED_PHRASE]
    blocked_topics = [r for r in rules if r.rule_type == ComplianceRuleType.BLOCKED_TOPIC]
    allowed_phrases = [r.value.lower() for r in rules if r.rule_type == ComplianceRuleType.ALLOWED_PHRASE]

    response_lower = response_text.lower()
    violations = []

    # Check blocked phrases
    for rule in blocked_phrases:
        if rule.value.lower() in response_lower:
            # Check if it's whitelisted by an allowed_phrase
            if not _is_whitelisted(rule.value.lower(), allowed_phrases):
                violations.append({
                    "rule_id": str(rule.id),
                    "rule_type": "blocked_phrase",
                    "value": rule.value,
                })

    # Check blocked topics
    for rule in blocked_topics:
        if rule.value.lower() in response_lower:
            if not _is_whitelisted(rule.value.lower(), allowed_phrases):
                violations.append({
                    "rule_id": str(rule.id),
                    "rule_type": "blocked_topic",
                    "value": rule.value,
                })

    # Check medical claim patterns
    medical_patterns = [
        (r'\b(cure|cures|curing)\b', "Medical claim: cure"),
        (r'\b(treat|treats|treating)\s+(acne|eczema|rosacea|psoriasis|dermatitis)', "Medical claim: treatment"),
        (r'\b(diagnos|prescri)', "Medical claim: diagnosis/prescription"),
        (r'\b(guaranteed|100%\s+effective)', "Unverifiable claim"),
        (r'\bFDA\s+approved\b', "Regulatory claim: FDA"),
        (r'\bclinically\s+proven\b', "Unverifiable claim: clinically proven"),
    ]

    for pattern, description in medical_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            matched_text = match.group()
            # Check if the matched text is whitelisted
            if not _is_whitelisted(matched_text.lower(), allowed_phrases):
                violations.append({
                    "rule_id": None,
                    "rule_type": "medical_pattern",
                    "value": description,
                })

    if violations:
        config_result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand_id))
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


def _is_whitelisted(text: str, allowed_phrases: list[str]) -> bool:
    """Check if flagged text is whitelisted. Only exact match or flagged text is substring of allowed."""
    for allowed in allowed_phrases:
        if text == allowed:
            return True
    return False


# Note: conversation_boundary rules are enforced via the system prompt (tone_service),
# not via post-response filtering. The AI is instructed to follow boundaries,
# and violations would need NLP analysis to detect (beyond simple pattern matching).
