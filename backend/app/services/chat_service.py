"""Main chat orchestrator. Full pipeline per SRS Section 3.1:
User message → Brand check → Moderation → RAG → Session state → Recommendation rules → Tone → LLM → Compliance → Response."""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand import Brand
from app.models.brand_config import BrandConfig
from app.models.conversation import Conversation, Message
from app.models.product import Product
from app.models.enums import (
    ChannelType, MessageRole, ChatbotStatus, ErrorType, ApiUsageType,
    SkinType, SkinConcern,
)
from app.models.logs import ComplianceLog, RAGRetrievalLog, APIUsageLog, ErrorLog, RecommendationRuleLog
from app.services import (
    llm_service, embedding_service, tone_service,
    compliance_service, moderation_service, recommendation_rule_service,
)
from app.core.exceptions import NotFoundError


async def process_message(
    db: AsyncSession,
    brand_id: UUID,
    session_id: str,
    user_message: str,
    channel: ChannelType = ChannelType.WEBSITE,
    ip_address: str | None = None,
    user_identifier: str | None = None,
) -> dict:
    """Process a user message through the full chatbot pipeline."""

    # Step 1: Validate brand
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand", str(brand_id))

    config_result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand_id))
    config = config_result.scalar_one_or_none()

    if brand.chatbot_status == ChatbotStatus.DISABLED:
        return _empty_response("This chatbot is currently disabled.", session_id, "disabled")
    if brand.chatbot_status == ChatbotStatus.SAFE_MODE:
        return _empty_response(config.fallback_message if config else "Please try again later.", session_id, "safe_mode")

    # Step 2: Input moderation
    mod_result = await moderation_service.moderate_input(
        db, brand_id, user_message,
        user_identifier=user_identifier or session_id,
        ip_address=ip_address,
    )
    if not mod_result["is_allowed"]:
        action = mod_result.get("action", "brand_fallback")
        if action == "silent_drop":
            return _empty_response("", session_id, "moderated")
        elif action == "polite_refusal":
            return _empty_response("I can only help with skincare-related questions.", session_id, "moderated")
        return _empty_response(config.fallback_message if config else "I can only help with skincare questions.", session_id, "moderated")

    # Step 3: Get or create conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.session_id == session_id, Conversation.brand_id == brand_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        conversation = Conversation(brand_id=brand_id, session_id=session_id, channel=channel, session_state={})
        db.add(conversation)
        await db.flush()

    # Step 4: Load session state (SRS Section 15 — session personalization)
    session_state = conversation.session_state or {}
    skin_type = session_state.get("skin_type")
    concerns = session_state.get("concerns", [])
    preferences = session_state.get("preferences", [])
    products_recommended = session_state.get("products_recommended", [])

    # Step 5: Extract skin profile from user message (simple keyword detection)
    skin_type, concerns, preferences = _update_profile_from_message(
        user_message, skin_type, concerns, preferences
    )

    # Step 6: Save user message
    user_msg = Message(conversation_id=conversation.id, role=MessageRole.USER, content=user_message)
    db.add(user_msg)
    await db.flush()

    # Step 7: RAG search
    rag_results = []
    threshold = config.rag_similarity_threshold if config else 0.7
    try:
        rag_results = await embedding_service.search_similar(db, brand_id, user_message, top_k=5, threshold=threshold)
    except Exception as e:
        db.add(ErrorLog(brand_id=brand_id, channel=channel, error_type=ErrorType.EMBEDDINGS_API_FAILURE, description=str(e)[:500]))

    db.add(RAGRetrievalLog(
        brand_id=brand_id, conversation_id=conversation.id, message_id=user_msg.id,
        user_query=user_message,
        chunks_retrieved=[{"entity_type": r["entity_type"], "entity_id": r["entity_id"], "similarity": r["similarity"], "excerpt": r["content"][:200]} for r in rag_results],
        chunks_retrieved_count=len(rag_results),
        top_similarity_score=rag_results[0]["similarity"] if rag_results else None,
        hit_threshold=len(rag_results) > 0,
    ))

    # Step 8: Apply recommendation rules if we have a skin profile (SRS Section 24)
    filtered_products = []
    rule_log_data = None
    if skin_type and any(r["entity_type"] == "product" for r in rag_results):
        try:
            skin_enum = SkinType(skin_type) if skin_type else None
            concern_enums = [SkinConcern(c) for c in concerns if c in [e.value for e in SkinConcern]]
            if skin_enum:
                rule_result = await recommendation_rule_service.test_rules(
                    db, brand_id, skin_enum, concern_enums, preferences
                )
                matched_ids = {p["product_id"] for p in rule_result.get("matched_products", [])}
                excluded_ids = {p["product_id"] for p in rule_result.get("excluded_products", [])}

                # Filter RAG results through recommendation rules
                for r in rag_results:
                    if r["entity_type"] == "product":
                        if r["entity_id"] in matched_ids and r["entity_id"] not in excluded_ids:
                            filtered_products.append(r)
                    else:
                        filtered_products.append(r)  # Keep FAQs/routines

                rule_log_data = rule_result

                # Log recommendation rule execution
                db.add(RecommendationRuleLog(
                    brand_id=brand_id, conversation_id=conversation.id, message_id=user_msg.id,
                    user_input_summary=user_message[:200],
                    skin_type=skin_enum,
                    concerns=[c.value for c in concern_enums],
                    matched_products=rule_result.get("matched_products", []),
                    matched_count=len(rule_result.get("matched_products", [])),
                    excluded_products=rule_result.get("excluded_products", []),
                    excluded_count=len(rule_result.get("excluded_products", [])),
                    applied_filters={"rules_applied": rule_result.get("rules_applied", 0)},
                ))
        except Exception:
            filtered_products = rag_results  # Rules failed — fall back to unfiltered RAG
    else:
        filtered_products = rag_results

    # Filter out already-recommended products (SRS Section 15.2 — no repeats)
    context_results = [
        r for r in filtered_products
        if r["entity_type"] != "product" or r["entity_id"] not in products_recommended
    ]

    # Step 9: Assemble system prompt + inject context
    system_prompt = await tone_service.assemble_system_prompt(db, brand_id)

    # Inject session state into prompt so AI knows what user already told us
    if skin_type or concerns or preferences:
        state_text = "\n\n[User Profile from this session — do NOT re-ask these]\n"
        if skin_type:
            state_text += f"- Skin type: {skin_type}\n"
        if concerns:
            state_text += f"- Concerns: {', '.join(concerns)}\n"
        if preferences:
            state_text += f"- Preferences: {', '.join(preferences)}\n"
        if products_recommended:
            state_text += f"- Already recommended (do NOT suggest again): {len(products_recommended)} products\n"
        system_prompt += state_text

    if context_results:
        context = "\n\n[Knowledge Base Context — answer ONLY from this information]\n"
        for r in context_results:
            context += f"- ({r['entity_type']}): {r['content']}\n"
        system_prompt += context
    else:
        system_prompt += "\n\n[No relevant context found. Use the fallback message.]"

    # Step 10: Build conversation history
    history = []
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id, Message.id != user_msg.id)
        .order_by(Message.created_at.desc()).limit(10)
    )
    for msg in reversed(msg_result.scalars().all()):
        history.append({"role": "assistant" if msg.role.value in ("assistant", "agent") else "user", "content": msg.content})
    history.append({"role": "user", "content": user_message})

    # Step 11: Call LLM
    max_tokens = config.max_tokens if config else 1000
    start_time = datetime.now(timezone.utc)
    llm_error = None

    try:
        llm_response = await llm_service.generate_response(system_prompt, history, max_tokens)
        ai_text = llm_response["content"]
        latency = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        db.add(APIUsageLog(
            brand_id=brand_id, conversation_id=conversation.id, api_type=ApiUsageType.CLAUDE,
            tokens_in=llm_response["tokens_in"], tokens_out=llm_response["tokens_out"],
            model=llm_response["model"], latency_ms=latency,
        ))
    except TimeoutError as e:
        llm_error = str(e)
        db.add(ErrorLog(brand_id=brand_id, channel=channel, error_type=ErrorType.TIMEOUT, description=llm_error))
        ai_text = config.fallback_message if config else "I couldn't process your request right now."
    except Exception as e:
        llm_error = str(e)[:500]
        db.add(ErrorLog(brand_id=brand_id, channel=channel, error_type=ErrorType.AI_API_FAILURE, description=llm_error))
        ai_text = config.fallback_message if config else "I couldn't process your request right now."

    # Step 12: Compliance filter
    compliance_clean = True
    if not llm_error:
        comp_result = await compliance_service.check_response(db, brand_id, ai_text)
        if not comp_result["is_clean"]:
            compliance_clean = False
            db.add(ComplianceLog(
                brand_id=brand_id, conversation_id=conversation.id, message_id=user_msg.id,
                original_response=comp_result["original_response"], replacement=comp_result["response"],
                reason=str(comp_result["violations"]),
            ))
            ai_text = comp_result["response"]

    # Step 13: Save AI response
    db.add(Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=ai_text))

    # Step 14: Update session state (persist skin profile + recommended products)
    new_recommended = [r["entity_id"] for r in context_results if r["entity_type"] == "product"]
    conversation.session_state = {
        "skin_type": skin_type,
        "concerns": concerns,
        "preferences": preferences,
        "products_recommended": list(set(products_recommended + new_recommended)),
    }
    await db.flush()

    # Step 15: Build product cards
    product_cards = []
    for r in context_results:
        if r["entity_type"] == "product":
            p_result = await db.execute(select(Product).where(Product.id == UUID(r["entity_id"])))
            product = p_result.scalar_one_or_none()
            if product:
                product_cards.append({
                    "product_id": str(product.id), "name": product.name,
                    "price": str(product.price), "currency": brand.currency,
                    "image_url": product.image_url, "purchase_url": product.purchase_url,
                    "category": product.category,
                })

    return {
        "response": ai_text,
        "conversation_id": str(conversation.id),
        "session_id": session_id,
        "type": "fallback" if llm_error else "ai",
        "rag_hits": len(rag_results),
        "compliance_clean": compliance_clean,
        "product_cards": product_cards,
        "session_state": {
            "skin_type": skin_type,
            "concerns": concerns,
            "preferences": preferences,
            "products_recommended_count": len(conversation.session_state.get("products_recommended", [])),
        },
    }


def _update_profile_from_message(
    message: str, skin_type: str | None, concerns: list, preferences: list
) -> tuple[str | None, list, list]:
    """Extract skin profile info from user message using keyword detection.
    SRS Section 15.1: Once user provides skin type, store in session."""
    msg_lower = message.lower()

    # Detect skin type
    skin_keywords = {
        "oily": "oily", "oil": "oily",
        "dry": "dry", "flaky": "dry",
        "combination": "combination", "combo": "combination",
        "sensitive": "sensitive",
        "normal": "normal",
    }
    for keyword, stype in skin_keywords.items():
        if keyword in msg_lower and not skin_type:
            skin_type = stype
            break

    # Detect concerns
    concern_keywords = {
        "acne": "acne", "pimple": "acne", "breakout": "acne",
        "aging": "aging", "wrinkle": "aging", "fine line": "aging", "anti-aging": "aging",
        "hydration": "hydration", "moistur": "hydration", "dehydrat": "hydration",
        "dark spot": "hyperpigmentation", "hyperpigmentation": "hyperpigmentation", "pigment": "hyperpigmentation", "uneven tone": "hyperpigmentation",
        "sensitive": "sensitivity", "irritat": "sensitivity", "redness": "sensitivity",
        "dull": "dullness", "glow": "dullness", "radian": "dullness", "bright": "dullness",
    }
    for keyword, concern in concern_keywords.items():
        if keyword in msg_lower and concern not in concerns:
            concerns.append(concern)

    # Detect preferences
    pref_keywords = {
        "fragrance-free": "fragrance-free", "no fragrance": "fragrance-free", "unscented": "fragrance-free",
        "vegan": "vegan", "cruelty-free": "cruelty-free",
        "budget": "budget-friendly", "affordable": "budget-friendly", "cheap": "budget-friendly",
        "natural": "natural", "organic": "organic",
    }
    for keyword, pref in pref_keywords.items():
        if keyword in msg_lower and pref not in preferences:
            preferences.append(pref)

    return skin_type, concerns, preferences


def _empty_response(text: str, session_id: str, resp_type: str) -> dict:
    return {
        "response": text, "conversation_id": None, "session_id": session_id,
        "type": resp_type, "rag_hits": 0, "compliance_clean": True,
        "product_cards": [], "session_state": None,
    }
