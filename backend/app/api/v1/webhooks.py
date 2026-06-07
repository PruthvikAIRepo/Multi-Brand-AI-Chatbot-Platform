"""Webhook endpoints for WhatsApp and Instagram.
Meta sends messages here → we process through chat pipeline → send response back via Meta API.

SRS Section 2.7: WhatsApp uses webhook-based integration. Instagram uses Meta Graph API.
Both use the same chat_service.process_message() pipeline — only the input/output format differs."""

import hashlib
import hmac
from uuid import UUID
from fastapi import APIRouter, Request, Query, HTTPException
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.brand import Brand
from app.models.enums import ChannelType
from app.services import chat_service, meta_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["Webhooks (WhatsApp + Instagram)"])


# --- Webhook Verification (required by Meta) ---

@router.get("/whatsapp/{brand_slug}")
async def verify_whatsapp_webhook(
    brand_slug: str,
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification. Called once when webhook URL is registered.
    Returns the challenge if the verify token matches."""
    if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.get("/instagram/{brand_slug}")
async def verify_instagram_webhook(
    brand_slug: str,
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification for Instagram."""
    if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


# --- WhatsApp Webhook Receiver ---

@router.post("/whatsapp/{brand_slug}")
async def receive_whatsapp_message(brand_slug: str, request: Request):
    """Receive incoming WhatsApp messages from Meta Cloud API.
    Processes through the full chat pipeline and sends response back via WhatsApp."""

    body = await request.json()

    # Extract message data from Meta's webhook format
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_messages"}  # Status updates, read receipts, etc.

        message = messages[0]
        sender_phone = message.get("from", "")
        message_text = message.get("text", {}).get("body", "")
        message_type = message.get("type", "")

        if message_type != "text" or not message_text:
            return {"status": "non_text_message"}  # We only handle text for now

    except (IndexError, KeyError, TypeError):
        return {"status": "invalid_payload"}

    # Resolve brand
    async with async_session_factory() as db:
        result = await db.execute(
            select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True)
        )
        brand = result.scalar_one_or_none()
        if not brand:
            return {"status": "brand_not_found"}

        # Process through the same pipeline as website chat
        session_id = f"wa_{sender_phone}"

        try:
            response = await chat_service.process_message(
                db=db,
                brand_id=brand.id,
                session_id=session_id,
                user_message=message_text,
                channel=ChannelType.WHATSAPP,
                user_identifier=sender_phone,
            )
            await db.commit()

            # Send response back via WhatsApp API
            if response.get("product_cards"):
                await meta_service.send_whatsapp_product_message(
                    db, brand.id, sender_phone,
                    response["response"], response["product_cards"]
                )
            else:
                await meta_service.send_whatsapp_message(
                    db, brand.id, sender_phone, response["response"]
                )

        except Exception:
            await db.rollback()
            # Send fallback on failure
            await meta_service.send_whatsapp_message(
                db, brand.id, sender_phone,
                "Sorry, I'm having trouble right now. Please try again."
            )

    return {"status": "processed"}


# --- Instagram Webhook Receiver ---

@router.post("/instagram/{brand_slug}")
async def receive_instagram_message(brand_slug: str, request: Request):
    """Receive incoming Instagram DMs from Meta Graph API.
    Processes through the full chat pipeline and sends response back via Instagram."""

    body = await request.json()

    # Extract message from Instagram webhook format
    try:
        entry = body.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender_id = messaging.get("sender", {}).get("id", "")
        message_data = messaging.get("message", {})
        message_text = message_data.get("text", "")

        if not message_text:
            return {"status": "non_text_message"}

    except (IndexError, KeyError, TypeError):
        return {"status": "invalid_payload"}

    # Resolve brand
    async with async_session_factory() as db:
        result = await db.execute(
            select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True)
        )
        brand = result.scalar_one_or_none()
        if not brand:
            return {"status": "brand_not_found"}

        # Process through the same pipeline
        session_id = f"ig_{sender_id}"

        try:
            response = await chat_service.process_message(
                db=db,
                brand_id=brand.id,
                session_id=session_id,
                user_message=message_text,
                channel=ChannelType.INSTAGRAM,
                user_identifier=sender_id,
            )
            await db.commit()

            # Send response back via Instagram API
            await meta_service.send_instagram_message(
                db, brand.id, sender_id, response["response"]
            )

        except Exception:
            await db.rollback()
            await meta_service.send_instagram_message(
                db, brand.id, sender_id,
                "Sorry, I'm having trouble right now. Please try again."
            )

    return {"status": "processed"}
