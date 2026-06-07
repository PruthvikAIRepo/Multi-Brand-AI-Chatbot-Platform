"""Main chat orchestrator. Ties together the full pipeline:
User message → Moderation → RAG search → Tone assembly → LLM → Compliance → Response."""

import uuid
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.brand import Brand
from app.models.brand_config import BrandConfig
from app.models.conversation import Conversation, Message
from app.models.enums import ChannelType, MessageRole, ChatbotStatus, EntityType
from app.models.logs import ComplianceLog, RAGRetrievalLog, APIUsageLog
from app.services import llm_service, embedding_service, tone_service, compliance_service
from app.core.exceptions import BadRequestError


async def process_message(
    db: AsyncSession,
    brand_id: UUID,
    session_id: str,
    user_message: str,
    channel: ChannelType = ChannelType.WEBSITE,
) -> dict:
    """Process a user message through the full chatbot pipeline."""

    # Step 1: Validate brand is active
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise BadRequestError("Brand not found")

    if brand.chatbot_status == ChatbotStatus.DISABLED:
        return {"response": "This chatbot is currently disabled.", "type": "disabled"}

    # Load config
    config_result = await db.execute(select(BrandConfig).where(BrandConfig.brand_id == brand_id))
    config = config_result.scalar_one_or_none()

    if brand.chatbot_status == ChatbotStatus.SAFE_MODE:
        fallback = config.fallback_message if config else "Please try again later."
        return {"response": fallback, "type": "safe_mode"}

    # Step 2: Get or create conversation
    conv_result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.session_id == session_id)
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

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Step 3: RAG search — find relevant products/FAQs
    rag_results = []
    threshold = config.rag_similarity_threshold if config else 0.7
    try:
        rag_results = await embedding_service.search_similar(
            db, brand_id, user_message, top_k=5, threshold=threshold
        )
    except Exception:
        pass  # RAG failure should not break chat — continue without context

    # Log RAG retrieval
    rag_log = RAGRetrievalLog(
        brand_id=brand_id,
        conversation_id=conversation.id,
        message_id=user_msg.id,
        user_query=user_message,
        chunks_retrieved=[
            {"entity_type": r["entity_type"], "entity_id": r["entity_id"],
             "similarity": r["similarity"], "excerpt": r["content"][:200]}
            for r in rag_results
        ],
        chunks_retrieved_count=len(rag_results),
        top_similarity_score=rag_results[0]["similarity"] if rag_results else None,
        hit_threshold=len(rag_results) > 0,
    )
    db.add(rag_log)

    # Step 4: Assemble system prompt
    system_prompt = await tone_service.assemble_system_prompt(db, brand_id)

    # Inject RAG context into prompt
    if rag_results:
        context_text = "\n\n[Knowledge Base Context — use ONLY this information to answer]\n"
        for r in rag_results:
            context_text += f"- ({r['entity_type']}): {r['content']}\n"
        system_prompt += context_text
    else:
        system_prompt += "\n\n[No relevant context found. Use the fallback message.]"

    # Step 5: Build conversation history for LLM
    history = []
    # Explicitly load recent messages (avoid lazy loading greenlet issue)
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.id != user_msg.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    recent_messages = msg_result.scalars().all()
    for msg in reversed(recent_messages):  # Reverse to chronological order
        history.append({"role": msg.role.value, "content": msg.content})

    history.append({"role": "user", "content": user_message})

    # Step 6: Call LLM
    max_tokens = config.max_tokens if config else 1000
    start_time = datetime.now(timezone.utc)

    try:
        llm_response = await llm_service.generate_response(
            system_prompt=system_prompt,
            messages=history,
            max_tokens=max_tokens,
        )
        ai_text = llm_response["content"]
        latency = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        # Log API usage
        db.add(APIUsageLog(
            brand_id=brand_id,
            conversation_id=conversation.id,
            api_type="claude" if "claude" in llm_response["model"] else "claude",
            tokens_in=llm_response["tokens_in"],
            tokens_out=llm_response["tokens_out"],
            model=llm_response["model"],
            latency_ms=latency,
        ))

    except Exception as e:
        # LLM failure — return fallback
        fallback = config.fallback_message if config else "I'm sorry, I couldn't process your request right now."
        ai_text = fallback

    # Step 7: Compliance filter
    compliance_result = await compliance_service.check_response(db, brand_id, ai_text)

    if not compliance_result["is_clean"]:
        # Log compliance violation
        db.add(ComplianceLog(
            brand_id=brand_id,
            conversation_id=conversation.id,
            message_id=user_msg.id,
            original_response=compliance_result["original_response"],
            replacement=compliance_result["response"],
            reason=str(compliance_result["violations"]),
        ))
        ai_text = compliance_result["response"]

    # Step 8: Save AI response
    ai_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=ai_text,
    )
    db.add(ai_msg)
    await db.flush()

    return {
        "response": ai_text,
        "conversation_id": str(conversation.id),
        "session_id": session_id,
        "type": "ai",
        "rag_hits": len(rag_results),
        "compliance_clean": compliance_result["is_clean"],
    }
