"""Webhook endpoints for WhatsApp and Instagram.
Meta sends messages here → we process async → send response back via Meta API.

Security: Verifies X-Hub-Signature-256 on every POST. Returns 200 immediately, processes async."""

import hashlib
import hmac
from uuid import UUID
from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.brand import Brand
from app.models.enums import ChannelType
from app.services import chat_service, meta_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["Webhooks (WhatsApp + Instagram)"])


# --- Signature Verification ---

def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 header using HMAC-SHA256."""
    if not settings.META_APP_SECRET:
        return True  # Skip verification if secret not configured (dev mode)
    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        settings.META_APP_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


# --- Webhook Verification (required by Meta) ---

@router.get("/whatsapp/{brand_slug}")
async def verify_whatsapp_webhook(
    brand_slug: str,
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification. Returns challenge if verify token matches."""
    if mode == "subscribe" and hmac.compare_digest(token or "", settings.META_WEBHOOK_VERIFY_TOKEN):
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
    if mode == "subscribe" and hmac.compare_digest(token or "", settings.META_WEBHOOK_VERIFY_TOKEN):
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


# --- WhatsApp Webhook Receiver ---

@router.post("/whatsapp/{brand_slug}")
async def receive_whatsapp_message(brand_slug: str, request: Request, background_tasks: BackgroundTasks):
    """Receive WhatsApp messages. Returns 200 immediately, processes async."""

    # Verify signature
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(raw_body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    import json
    body = json.loads(raw_body)

    # Extract message
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}  # Status updates, read receipts

        message = messages[0]
        sender_phone = message.get("from", "")
        message_text = message.get("text", {}).get("body", "")

        if message.get("type") != "text" or not message_text:
            return {"status": "ok"}

    except (IndexError, KeyError, TypeError):
        return {"status": "ok"}

    # Return 200 immediately — process in background (Meta requires fast response)
    background_tasks.add_task(
        _process_whatsapp_message, brand_slug, sender_phone, message_text
    )

    return {"status": "ok"}


async def _process_whatsapp_message(brand_slug: str, sender_phone: str, message_text: str):
    """Background task: process WhatsApp message through chat pipeline."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            if not brand:
                return

            # Brand-scoped session ID (prevents cross-brand contamination)
            session_id = f"wa_{brand.id}_{sender_phone}"

            response = await chat_service.process_message(
                db=db, brand_id=brand.id, session_id=session_id,
                user_message=message_text, channel=ChannelType.WHATSAPP,
                user_identifier=sender_phone,
            )
            await db.commit()

            # Send response back
            try:
                await meta_service.send_whatsapp_message(
                    db, brand.id, sender_phone, response["response"]
                )
            except Exception:
                pass  # Send failure doesn't affect message processing

        except Exception:
            await db.rollback()


# --- Instagram Webhook Receiver ---

@router.post("/instagram/{brand_slug}")
async def receive_instagram_message(brand_slug: str, request: Request, background_tasks: BackgroundTasks):
    """Receive Instagram DMs. Returns 200 immediately, processes async."""

    # Verify signature
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(raw_body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    import json
    body = json.loads(raw_body)

    # Extract message
    try:
        entry = body.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender_id = messaging.get("sender", {}).get("id", "")
        message_text = messaging.get("message", {}).get("text", "")

        if not message_text:
            return {"status": "ok"}

    except (IndexError, KeyError, TypeError):
        return {"status": "ok"}

    # Return 200 immediately — process in background
    background_tasks.add_task(
        _process_instagram_message, brand_slug, sender_id, message_text
    )

    return {"status": "ok"}


async def _process_instagram_message(brand_slug: str, sender_id: str, message_text: str):
    """Background task: process Instagram message through chat pipeline."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            if not brand:
                return

            session_id = f"ig_{brand.id}_{sender_id}"

            response = await chat_service.process_message(
                db=db, brand_id=brand.id, session_id=session_id,
                user_message=message_text, channel=ChannelType.INSTAGRAM,
                user_identifier=sender_id,
            )
            await db.commit()

            try:
                await meta_service.send_instagram_message(
                    db, brand.id, sender_id, response["response"]
                )
            except Exception:
                pass

        except Exception:
            await db.rollback()
