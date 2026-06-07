import csv
import io
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead
from app.models.enums import ChannelType
from app.core.encryption import encrypt, decrypt, hash_value, mask_email, mask_phone
from app.core.exceptions import NotFoundError


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def create_or_update_lead(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Create a lead or update existing one (matched by email hash). SRS: dedup by email."""
    email = data["email"].lower().strip()
    email_hashed = hash_value(email)

    # Check for existing lead with same email in same brand
    result = await db.execute(
        select(Lead).where(
            Lead.brand_id == brand_id,
            Lead.email_hash == email_hashed,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing lead
        existing.name = data["name"]
        existing.email_encrypted = encrypt(email)
        if data.get("phone"):
            existing.phone_encrypted = encrypt(data["phone"])
        existing.consent = data.get("consent", True)
        existing.consent_text = data.get("consent_text")
        if data.get("conversation_id"):
            existing.conversation_id = data["conversation_id"]
        await db.flush()
        # Decrypt existing phone if update didn't provide one
        phone = data.get("phone")
        if not phone and existing.phone_encrypted:
            phone = decrypt(existing.phone_encrypted)
        return _lead_to_dict(existing, email, phone)

    # Create new lead
    lead = Lead(
        brand_id=brand_id,
        name=data["name"],
        email_encrypted=encrypt(email),
        email_hash=email_hashed,
        phone_encrypted=encrypt(data["phone"]) if data.get("phone") else None,
        channel=data["channel"],
        consent=data.get("consent", True),
        consent_text=data.get("consent_text"),
        conversation_id=data.get("conversation_id"),
    )
    db.add(lead)
    await db.flush()
    return _lead_to_dict(lead, email, data.get("phone"))


async def list_leads(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    channel: ChannelType | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    """List leads with masked PII. Search by name only (email is encrypted)."""
    base_filter = [Lead.brand_id == brand_id]

    if channel:
        base_filter.append(Lead.channel == channel)
    if search:
        safe = _escape_like(search)
        base_filter.append(Lead.name.ilike(f"%{safe}%"))

    count_result = await db.execute(
        select(func.count()).select_from(Lead).where(*base_filter)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Lead)
        .where(*base_filter)
        .order_by(Lead.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    leads = result.scalars().all()

    # Decrypt for masked display
    data = []
    for lead in leads:
        email = decrypt(lead.email_encrypted)
        phone = decrypt(lead.phone_encrypted) if lead.phone_encrypted else None
        data.append(_lead_to_masked_dict(lead, email, phone))

    return data, total


async def get_lead(db: AsyncSession, brand_id: UUID, lead_id: UUID) -> dict:
    """Get a single lead with FULL decrypted PII (for authorized admin viewing)."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.brand_id == brand_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    email = decrypt(lead.email_encrypted)
    phone = decrypt(lead.phone_encrypted) if lead.phone_encrypted else None
    return _lead_to_dict(lead, email, phone)


async def delete_lead(db: AsyncSession, brand_id: UUID, lead_id: UUID) -> None:
    """GDPR: Permanently delete a lead."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.brand_id == brand_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    await db.delete(lead)
    await db.flush()


async def export_leads_csv(
    db: AsyncSession,
    brand_id: UUID,
    channel: ChannelType | None = None,
) -> str:
    """Export leads as CSV string. Decrypts PII for export."""
    base_filter = [Lead.brand_id == brand_id]
    if channel:
        base_filter.append(Lead.channel == channel)

    result = await db.execute(
        select(Lead).where(*base_filter).order_by(Lead.created_at.desc())
    )
    leads = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "phone", "channel", "consent", "created_at"])

    for lead in leads:
        email = decrypt(lead.email_encrypted)
        phone = decrypt(lead.phone_encrypted) if lead.phone_encrypted else ""
        writer.writerow([
            lead.name, email, phone,
            lead.channel.value if lead.channel else "",
            lead.consent,
            lead.created_at.isoformat() if lead.created_at else "",
        ])

    return output.getvalue()


# --- Helpers ---

def _lead_to_dict(lead: Lead, email: str, phone: str | None) -> dict:
    """Full PII — for detail view."""
    return {
        "id": str(lead.id),
        "brand_id": str(lead.brand_id),
        "name": lead.name,
        "email": email,
        "phone": phone,
        "channel": lead.channel.value if lead.channel else None,
        "consent": lead.consent,
        "consent_text": lead.consent_text,
        "conversation_id": str(lead.conversation_id) if lead.conversation_id else None,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def _lead_to_masked_dict(lead: Lead, email: str, phone: str | None) -> dict:
    """Masked PII — for list view."""
    return {
        "id": str(lead.id),
        "brand_id": str(lead.brand_id),
        "name": lead.name,
        "email_masked": mask_email(email),
        "phone_masked": mask_phone(phone) if phone else None,
        "channel": lead.channel.value if lead.channel else None,
        "consent": lead.consent,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }
