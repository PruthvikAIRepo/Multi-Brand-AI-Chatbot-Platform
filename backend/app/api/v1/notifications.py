from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import notification_service
from app.core.permissions import get_current_user
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current user (includes broadcasts)."""
    data, total = await notification_service.list_notifications(
        db, current_user.id, page, per_page, unread_only
    )
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count (for bell badge)."""
    count = await notification_service.get_unread_count(db, current_user.id)
    return api_response(data={"unread_count": count})


@router.post("/{notification_id}/read", response_model=dict)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notif = await notification_service.mark_as_read(db, notification_id, current_user.id)
    return api_response(data=notif, message="Marked as read")


@router.post("/read-all", response_model=dict)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(db, current_user.id)
    return api_response(data={"marked_count": count}, message=f"{count} notifications marked as read")
