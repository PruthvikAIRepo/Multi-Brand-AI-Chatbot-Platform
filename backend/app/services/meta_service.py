"""Meta Platform API service — sends messages via WhatsApp Cloud API and Instagram Graph API.
Used by webhook handlers to send AI responses back to users."""

import httpx
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.secret_service import resolve_api_key
from app.models.enums import SecretType


async def send_whatsapp_message(db: AsyncSession, brand_id: UUID, phone_number: str, text: str) -> bool:
    """Send a text message via WhatsApp Cloud API.
    Uses the brand's Meta WhatsApp token (or system default)."""

    token = await resolve_api_key(db, brand_id, SecretType.META_WHATSAPP_TOKEN)
    if not token:
        return False

    # WhatsApp Cloud API expects: phone_number_id in the URL
    # The token includes access to the phone number
    # For now, we use the token as the access token and the phone_number_id
    # should be stored in channel_configs (Phase 2 table)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {"body": text},
                },
            )
            return response.status_code == 200
    except Exception:
        return False


async def send_whatsapp_product_message(
    db: AsyncSession, brand_id: UUID, phone_number: str, text: str, products: list[dict]
) -> bool:
    """Send a message with product info via WhatsApp (text + image per product)."""
    # First send the text response
    sent = await send_whatsapp_message(db, brand_id, phone_number, text)
    if not sent:
        return False

    # Send product images as separate media messages
    token = await resolve_api_key(db, brand_id, SecretType.META_WHATSAPP_TOKEN)
    if not token:
        return True  # Text sent, media failed — acceptable

    for product in products[:3]:  # Max 3 products for WhatsApp
        if product.get("image_url"):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"https://graph.facebook.com/v18.0/me/messages",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "messaging_product": "whatsapp",
                            "to": phone_number,
                            "type": "image",
                            "image": {
                                "link": product["image_url"],
                                "caption": f"{product['name']} - {product.get('currency', '')} {product.get('price', '')}",
                            },
                        },
                    )
            except Exception:
                pass  # Individual image failures don't block

    return True


async def send_instagram_message(db: AsyncSession, brand_id: UUID, recipient_id: str, text: str) -> bool:
    """Send a message via Instagram Graph API."""

    token = await resolve_api_key(db, brand_id, SecretType.META_INSTAGRAM_TOKEN)
    if not token:
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": text},
                },
            )
            return response.status_code == 200
    except Exception:
        return False
