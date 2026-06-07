"""Main chat orchestrator. Full pipeline per SRS Section 3.1:
User message → Brand check → Moderation → RAG search → Tone assembly → LLM (timeout+retry) → Compliance → Response."""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand import Brand
from app.models.brand_config import BrandConfig
from app.models.conversation import Conversation, Message
from app.models.enums import ChannelType, MessageRole, ChatbotStatus, ErrorType, ApiUsageType
from app.models.logs import ComplianceLog, RAGRetrievalLog, APIUsageLog, ErrorLog
from app.services import llm_service, embedding_service, tone_service, compliance_service, moderation_service
from app.core.exceptions import NotFoundError


async def process_message(
    db: AsyncSession,
    brand_id: UUID,
    session_id: str,
    user_message: str,
    channel: ChannelType = ChannelType.WEBSITE,
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
        fallback = config.fallback_message if config else "Please try again later."
        return _empty_response(fallback, session_id, "safe_mode")

    # Step 2: Input moderation — block spam/abuse/injection BEFORE any LLM call (saves tokens)
    moderation_result = await moderation_service.moderate_input(
        db, brand_id, user_message,
        user_identifier=None,  # Set from request context if available
        ip_address=None,       # Set from request context if available
    )
    if not moderation_result["is_allowed"]:
        from app.models.enums import ModerationResponse
        action = moderation_result.get("action", "brand_fallback")
        if action == "silent_drop":
            return _empty_response("", session_id, "moderated")
        elif action == "polite_refusal":
            return _empty_response("I can only help with skincare-related questions.", session_id, "moderated")
        else:
            fallback = config.fallback_message if config else "I can only help with skincare-related questions."
            return _empty_response(fallback, session_id, "moderated")

    # Step 3: Get or create conversation (brand_id filter prevents cross-brand contamination)
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.brand_id == brand_id,
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            brand_id=brand_id,
            session_id=session_id,
            channel=channel,
        )
        db.add(conversation)
        await db.flush()

    # Step 3: Save user message
    user_msg = Message(conversation_id=conversation.id, role=MessageRole.USER, content=user_message)
    db.add(user_msg)
    await db.flush()

    # Step 4: RAG search
    rag_results = []
    threshold = config.rag_similarity_threshold if config else 0.7
    try:
        rag_results = await embedding_service.search_similar(
            db, brand_id, user_message, top_k=5, threshold=threshold
        )
    except Exception as e:
        db.add(ErrorLog(
            brand_id=brand_id, channel=channel,
            error_type=ErrorType.EMBEDDINGS_API_FAILURE,
            description=f"RAG search failed: {str(e)[:500]}",
        ))

    # Log RAG retrieval
    db.add(RAGRetrievalLog(
        brand_id=brand_id, conversation_id=conversation.id, message_id=user_msg.id,
        user_query=user_message,
        chunks_retrieved=[
            {"entity_type": r["entity_type"], "entity_id": r["entity_id"],
             "similarity": r["similarity"], "excerpt": r["content"][:200]}
            for r in rag_results
        ],
        chunks_retrieved_count=len(rag_results),
        top_similarity_score=rag_results[0]["similarity"] if rag_results else None,
        hit_threshold=len(rag_results) > 0,
    ))

    # Step 5: Assemble system prompt + inject RAG context
    system_prompt = await tone_service.assemble_system_prompt(db, brand_id)
    if rag_results:
        context = "\n\n[Knowledge Base Context — answer ONLY from this information]\n"
        for r in rag_results:
            context += f"- ({r['entity_type']}): {r['content']}\n"
        system_prompt += context
    else:
        system_prompt += "\n\n[No relevant context found. Use the fallback message.]"

    # Step 6: Build conversation history (last 10 messages)
    history = []
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.id != user_msg.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    for msg in reversed(msg_result.scalars().all()):
        role = "assistant" if msg.role.value in ("assistant", "agent") else "user"
        history.append({"role": role, "content": msg.content})
    history.append({"role": "user", "content": user_message})

    # Step 7: Call LLM (8-second timeout, 1 retry)
    max_tokens = config.max_tokens if config else 1000
    start_time = datetime.now(timezone.utc)
    llm_error = None

    try:
        llm_response = await llm_service.generate_response(system_prompt, history, max_tokens)
        ai_text = llm_response["content"]
        latency = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        db.add(APIUsageLog(
            brand_id=brand_id, conversation_id=conversation.id,
            api_type=ApiUsageType.CLAUDE,
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

    # Step 8: Compliance filter
    compliance_clean = True
    if not llm_error:
        compliance_result = await compliance_service.check_response(db, brand_id, ai_text)
        if not compliance_result["is_clean"]:
            compliance_clean = False
            db.add(ComplianceLog(
                brand_id=brand_id, conversation_id=conversation.id, message_id=user_msg.id,
                original_response=compliance_result["original_response"],
                replacement=compliance_result["response"],
                reason=str(compliance_result["violations"]),
            ))
            ai_text = compliance_result["response"]

    # Step 9: Save AI response
    db.add(Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=ai_text))
    await db.flush()

    # Step 10: Build product cards from RAG results
    product_cards = []
    for r in rag_results:
        if r["entity_type"] == "product":
            from app.models.product import Product
            p_result = await db.execute(select(Product).where(Product.id == UUID(r["entity_id"])))
            product = p_result.scalar_one_or_none()
            if product:
                product_cards.append({
                    "product_id": str(product.id),
                    "name": product.name,
                    "price": str(product.price),
                    "currency": brand.currency,
                    "image_url": product.image_url,
                    "purchase_url": product.purchase_url,
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
    }


def _empty_response(text: str, session_id: str, resp_type: str) -> dict:
    return {
        "response": text, "conversation_id": None, "session_id": session_id,
        "type": resp_type, "rag_hits": 0, "compliance_clean": True, "product_cards": [],
    }
