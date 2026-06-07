"""Audit trail service. Logs every admin action to admin_activity_logs.
SRS Critical Rule #10: Audit everything — who/what/when/before/after."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.logs import AdminActivityLog
from app.models.enums import AdminActionType


async def log_action(
    db: AsyncSession,
    user_id: UUID,
    action_type: AdminActionType,
    entity_type: str,
    entity_id: UUID | None = None,
    entity_name: str | None = None,
    brand_id: UUID | None = None,
    ip_address: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
) -> None:
    """Log an admin action. Call this from any service/route that modifies data."""
    db.add(AdminActivityLog(
        user_id=user_id,
        brand_id=brand_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        ip_address=ip_address,
        before_state=before_state,
        after_state=after_state,
    ))
