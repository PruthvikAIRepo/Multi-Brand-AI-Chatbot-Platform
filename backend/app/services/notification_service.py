from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from app.models.enums import NotificationType
from app.core.exceptions import NotFoundError


async def create_notification(
    db: AsyncSession,
    user_id: UUID | None,
    brand_id: UUID | None,
    notification_type: NotificationType,
    title: str,
    message: str,
    action_url: str | None = None,
) -> dict:
    """Create a notification. user_id=None broadcasts to all."""
    notif = Notification(
        user_id=user_id,
        brand_id=brand_id,
        notification_type=notification_type,
        title=title,
        message=message,
        action_url=action_url,
    )
    db.add(notif)
    await db.flush()
    return _notif_to_dict(notif)


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
) -> tuple[list[dict], int]:
    """List notifications for a user (includes broadcasts where user_id is NULL)."""
    filters = [
        (Notification.user_id == user_id) | (Notification.user_id.is_(None))
    ]
    if unread_only:
        filters.append(Notification.is_read == False)

    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    notifs = result.scalars().all()

    return [_notif_to_dict(n) for n in notifs], total


async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
    """Get unread notification count for the bell badge."""
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
            Notification.is_read == False,
        )
    )
    return result.scalar()


async def mark_as_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> dict:
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise NotFoundError("Notification", str(notification_id))

    notif.is_read = True
    await db.flush()
    return _notif_to_dict(notif)


async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> int:
    """Mark all notifications as read for a user. Returns count updated."""
    result = await db.execute(
        select(Notification).where(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
            Notification.is_read == False,
        )
    )
    notifs = result.scalars().all()
    count = 0
    for n in notifs:
        n.is_read = True
        count += 1
    await db.flush()
    return count


def _notif_to_dict(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "user_id": str(n.user_id) if n.user_id else None,
        "brand_id": str(n.brand_id) if n.brand_id else None,
        "notification_type": n.notification_type.value if n.notification_type else None,
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "action_url": n.action_url,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
