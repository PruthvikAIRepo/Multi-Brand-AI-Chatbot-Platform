"""WebSocket chat endpoint for real-time chatbot communication.
SRS Section 2.7: Website Chat uses WebSocket for live bidirectional messaging."""

import uuid
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.brand import Brand
from app.models.enums import ChannelType
from app.services import chat_service
from app.core.rate_limiter import check_chat_rate_limit

router = APIRouter(tags=["WebSocket Chat"])


@router.websocket("/ws/chat/{brand_slug}")
async def websocket_chat(websocket: WebSocket, brand_slug: str):
    """WebSocket endpoint for real-time chat. No auth — public for chat widget.

    Protocol:
    - Client connects to /ws/chat/{brand_slug}
    - Client sends JSON: {"message": "...", "session_id": "..." (optional)}
    - Server responds JSON: {"response": "...", "product_cards": [...], ...}
    - Connection stays open for multiple messages
    """
    # Resolve brand before accepting connection
    async with async_session_factory() as db:
        result = await db.execute(
            select(Brand).where(Brand.slug == brand_slug, Brand.is_active == True)
        )
        brand = result.scalar_one_or_none()

    if not brand:
        await websocket.close(code=4004, reason="Brand not found or inactive")
        return

    await websocket.accept()

    # Generate session_id for this WebSocket connection
    session_id = f"ws_{uuid.uuid4().hex[:16]}"
    client_ip = websocket.client.host if websocket.client else None

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "brand_name": brand.name,
            "session_id": session_id,
        })

        while True:
            # Receive message from client
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            if len(message) > 2000:
                await websocket.send_json({"type": "error", "message": "Message too long (max 2000 chars)"})
                continue

            # Use session_id from client if provided (reconnection support)
            client_session = data.get("session_id", session_id)

            # Rate limit check
            rate_check = await check_chat_rate_limit(ip_address=client_ip, session_id=client_session)
            if rate_check:
                await websocket.send_json({"type": "rate_limited", "message": rate_check["message"]})
                continue

            # Send typing indicator
            await websocket.send_json({"type": "typing"})

            # Process through the full pipeline
            async with async_session_factory() as db:
                try:
                    response = await chat_service.process_message(
                        db=db,
                        brand_id=brand.id,
                        session_id=client_session,
                        user_message=message,
                        channel=ChannelType.WEBSITE,
                        ip_address=client_ip,
                    )
                    await db.commit()

                    await websocket.send_json({
                        "type": "message",
                        **response,
                    })
                except Exception as e:
                    await db.rollback()
                    await websocket.send_json({
                        "type": "error",
                        "message": "Something went wrong. Please try again.",
                    })

    except WebSocketDisconnect:
        pass  # Client disconnected — clean exit
    except Exception:
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
