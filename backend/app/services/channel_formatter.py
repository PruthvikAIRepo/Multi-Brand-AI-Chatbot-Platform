"""Channel-specific response formatting. SRS Section 14.
Website: Rich HTML with product cards, routine cards, quick-action buttons.
WhatsApp: Concise, plain text, minimal formatting.
Instagram: Short, conversational, emoji-friendly if brand allows."""

from app.models.enums import ChannelType


def format_response(
    ai_text: str,
    product_cards: list[dict],
    channel: ChannelType,
    emoji_allowed: bool = False,
) -> dict:
    """Format the AI response for the target channel."""
    if channel == ChannelType.WEBSITE:
        return _format_website(ai_text, product_cards)
    elif channel == ChannelType.WHATSAPP:
        return _format_whatsapp(ai_text, product_cards)
    elif channel == ChannelType.INSTAGRAM:
        return _format_instagram(ai_text, product_cards, emoji_allowed)
    return _format_website(ai_text, product_cards)


def _format_website(ai_text: str, product_cards: list[dict]) -> dict:
    """Website: full rich response with product cards."""
    return {
        "text": ai_text,
        "format": "rich",
        "product_cards": product_cards,
        "quick_replies": [],
    }


def _format_whatsapp(ai_text: str, product_cards: list[dict]) -> dict:
    """WhatsApp: plain text, concise. Product info as inline text, not cards."""
    lines = [ai_text]

    if product_cards:
        lines.append("")
        for card in product_cards[:3]:  # Max 3 products for WhatsApp
            price_str = f"{card.get('currency', '')} {card.get('price', '')}".strip()
            lines.append(f"*{card['name']}* - {price_str}")
            if card.get("purchase_url"):
                lines.append(f"Shop: {card['purchase_url']}")
            lines.append("")

    return {
        "text": "\n".join(lines).strip(),
        "format": "plain",
        "product_cards": [],  # WhatsApp sends products as text, not cards
        "quick_replies": [],
    }


def _format_instagram(ai_text: str, product_cards: list[dict], emoji_allowed: bool) -> dict:
    """Instagram: short, conversational. Max 2 products."""
    # Truncate response for Instagram brevity
    text = ai_text
    if len(text) > 500:
        text = text[:497] + "..."

    product_lines = []
    if product_cards:
        for card in product_cards[:2]:  # Max 2 for Instagram
            name = card["name"]
            price = f"{card.get('currency', '')} {card.get('price', '')}".strip()
            product_lines.append(f"{name} ({price})")

    if product_lines:
        text += "\n\n" + " | ".join(product_lines)

    return {
        "text": text,
        "format": "plain",
        "product_cards": [],  # Instagram sends as text
        "quick_replies": [],
    }
