"""Input moderation pipeline. Runs BEFORE any LLM call. SRS Section 20.
Blocks spam, abuse, prompt injection — saves Claude/OpenAI API costs."""

import re
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.moderation_config import ModerationConfig
from app.models.bot_protection import IPBlockList, UserBlockList
from app.models.logs import ModerationLog
from app.models.enums import ModerationReason, ModerationResponse, ModerationSensitivity


# Prompt injection patterns — common attack signatures
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(a|an|the)",
    r"forget\s+(your|all|previous)\s+(instructions|rules|prompt)",
    r"(system|developer)\s*prompt",
    r"reveal\s+(your|the)\s+(instructions|prompt|rules|system)",
    r"act\s+as\s+(if|though)\s+you",
    r"pretend\s+(you|to\s+be)",
    r"(jailbreak|DAN|do\s+anything\s+now)",
    r"override\s+(your|the)\s+(rules|instructions|safety)",
    r"(disregard|bypass)\s+(all|your|the)\s+(rules|safety|instructions)",
]

# Abuse/profanity patterns (basic — production should use a proper word list)
ABUSE_PATTERNS = [
    r"\b(fuck|shit|bitch|ass|damn|bastard|dick|pussy)\b",
    r"\b(kill|murder|die|suicide|harm)\b",
    r"\b(hate\s+you|stupid\s+bot|useless)\b",
]

# Gibberish detection — low character entropy
def _is_gibberish(text: str) -> bool:
    """Detect gibberish by checking character variety."""
    if len(text) < 3:
        return False
    unique_chars = len(set(text.lower().replace(" ", "")))
    if unique_chars <= 2 and len(text) > 10:
        return True
    # Repeated character sequences
    if re.match(r'^(.)\1{5,}$', text.strip()):
        return True
    return False


async def moderate_input(
    db: AsyncSession,
    brand_id: UUID,
    user_message: str,
    user_identifier: str | None = None,
    ip_address: str | None = None,
    conversation_id: UUID | None = None,
) -> dict:
    """Run the moderation pipeline on user input.
    Returns {is_allowed, reason, action} if blocked, or {is_allowed: True} if clean."""

    # Step 1: Load brand moderation config
    config_result = await db.execute(
        select(ModerationConfig).where(ModerationConfig.brand_id == brand_id)
    )
    config = config_result.scalar_one_or_none()
    sensitivity = config.sensitivity if config else ModerationSensitivity.MEDIUM
    response_on_block = config.response_on_block if config else ModerationResponse.BRAND_FALLBACK

    # Step 2: Check IP block list
    if ip_address:
        ip_result = await db.execute(
            select(IPBlockList).where(
                IPBlockList.ip_address == ip_address,
                (IPBlockList.brand_id == brand_id) | (IPBlockList.brand_id.is_(None)),
            )
        )
        if ip_result.scalar_one_or_none():
            return await _block(db, brand_id, conversation_id, user_identifier,
                                user_message, ModerationReason.ABUSE, response_on_block,
                                "Blocked IP address")

    # Step 3: Check user block list
    if user_identifier:
        user_result = await db.execute(
            select(UserBlockList).where(
                UserBlockList.user_identifier == user_identifier,
                (UserBlockList.brand_id == brand_id) | (UserBlockList.brand_id.is_(None)),
            )
        )
        if user_result.scalar_one_or_none():
            return await _block(db, brand_id, conversation_id, user_identifier,
                                user_message, ModerationReason.ABUSE, response_on_block,
                                "Blocked user")

    # Step 4: Pre-filter — empty, too short, too long
    stripped = user_message.strip()
    if len(stripped) == 0:
        return await _block(db, brand_id, conversation_id, user_identifier,
                            user_message, ModerationReason.SPAM, response_on_block,
                            "Empty message")

    # Step 5: Gibberish detection
    if _is_gibberish(stripped):
        return await _block(db, brand_id, conversation_id, user_identifier,
                            user_message, ModerationReason.SPAM, response_on_block,
                            "Gibberish detected")

    # Step 6: Prompt injection detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return await _block(db, brand_id, conversation_id, user_identifier,
                                user_message, ModerationReason.PROMPT_INJECTION, response_on_block,
                                f"Prompt injection pattern: {pattern}")

    # Step 7: Check admin-defined block list
    if config and config.block_list:
        for blocked in config.block_list:
            if blocked.lower() in user_message.lower():
                return await _block(db, brand_id, conversation_id, user_identifier,
                                    user_message, ModerationReason.ABUSE, response_on_block,
                                    f"Blocked phrase: {blocked}")

    # Step 8: Check admin-defined injection patterns
    if config and config.prompt_injection_patterns:
        for pattern in config.prompt_injection_patterns:
            try:
                if re.search(pattern, user_message, re.IGNORECASE):
                    return await _block(db, brand_id, conversation_id, user_identifier,
                                        user_message, ModerationReason.PROMPT_INJECTION, response_on_block,
                                        f"Custom injection pattern: {pattern}")
            except re.error:
                pass  # Invalid regex in admin config — skip

    # Step 9: Abuse/profanity filter (sensitivity-based)
    if sensitivity in (ModerationSensitivity.MEDIUM, ModerationSensitivity.HIGH):
        for pattern in ABUSE_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return await _block(db, brand_id, conversation_id, user_identifier,
                                    user_message, ModerationReason.ABUSE, response_on_block,
                                    f"Abusive content detected")

    # All checks passed
    return {"is_allowed": True}


async def _block(
    db: AsyncSession,
    brand_id: UUID,
    conversation_id: UUID | None,
    user_identifier: str | None,
    blocked_input: str,
    reason: ModerationReason,
    action: ModerationResponse,
    description: str,
) -> dict:
    """Log blocked input and return block response."""
    db.add(ModerationLog(
        brand_id=brand_id,
        conversation_id=conversation_id,
        user_identifier=user_identifier,
        blocked_input=blocked_input[:2000],
        reason=reason,
        action_taken=action,
    ))
    await db.flush()

    return {
        "is_allowed": False,
        "reason": reason.value,
        "action": action.value,
        "description": description,
    }
