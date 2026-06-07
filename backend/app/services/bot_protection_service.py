from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.bot_protection import IPBlockList, UserBlockList
from app.core.exceptions import NotFoundError, AlreadyExistsError


async def block_ip(db: AsyncSession, ip_address: str, brand_id: UUID | None, blocked_by: UUID, reason: str | None) -> dict:
    # Check if already blocked
    result = await db.execute(
        select(IPBlockList).where(
            IPBlockList.ip_address == ip_address,
            IPBlockList.brand_id == brand_id,
        )
    )
    if result.scalar_one_or_none():
        raise AlreadyExistsError("IP block", "ip_address", ip_address)

    entry = IPBlockList(
        ip_address=ip_address,
        brand_id=brand_id,
        blocked_by=blocked_by,
        reason=reason,
    )
    db.add(entry)
    await db.flush()
    return _ip_to_dict(entry)


async def list_blocked_ips(
    db: AsyncSession, page: int = 1, per_page: int = 20, brand_id: UUID | None = None,
) -> tuple[list[dict], int]:
    filters = []
    if brand_id:
        filters.append(IPBlockList.brand_id == brand_id)

    count_query = select(func.count()).select_from(IPBlockList)
    data_query = select(IPBlockList).order_by(IPBlockList.created_at.desc())

    if filters:
        count_query = count_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        data_query.offset((page - 1) * per_page).limit(per_page)
    )
    return [_ip_to_dict(e) for e in result.scalars().all()], total


async def unblock_ip(db: AsyncSession, entry_id: UUID) -> None:
    result = await db.execute(select(IPBlockList).where(IPBlockList.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundError("IP block entry", str(entry_id))
    await db.delete(entry)
    await db.flush()


async def block_user(db: AsyncSession, user_identifier: str, brand_id: UUID | None, blocked_by: UUID, reason: str | None) -> dict:
    result = await db.execute(
        select(UserBlockList).where(
            UserBlockList.user_identifier == user_identifier,
            UserBlockList.brand_id == brand_id,
        )
    )
    if result.scalar_one_or_none():
        raise AlreadyExistsError("User block", "user_identifier", user_identifier)

    entry = UserBlockList(
        user_identifier=user_identifier,
        brand_id=brand_id,
        blocked_by=blocked_by,
        reason=reason,
    )
    db.add(entry)
    await db.flush()
    return _user_block_to_dict(entry)


async def list_blocked_users(
    db: AsyncSession, page: int = 1, per_page: int = 20, brand_id: UUID | None = None,
) -> tuple[list[dict], int]:
    filters = []
    if brand_id:
        filters.append(UserBlockList.brand_id == brand_id)

    count_query = select(func.count()).select_from(UserBlockList)
    data_query = select(UserBlockList).order_by(UserBlockList.created_at.desc())

    if filters:
        count_query = count_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        data_query.offset((page - 1) * per_page).limit(per_page)
    )
    return [_user_block_to_dict(e) for e in result.scalars().all()], total


async def unblock_user(db: AsyncSession, entry_id: UUID) -> None:
    result = await db.execute(select(UserBlockList).where(UserBlockList.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundError("User block entry", str(entry_id))
    await db.delete(entry)
    await db.flush()


def _ip_to_dict(e: IPBlockList) -> dict:
    return {
        "id": str(e.id), "ip_address": e.ip_address,
        "brand_id": str(e.brand_id) if e.brand_id else None,
        "blocked_by": str(e.blocked_by) if e.blocked_by else None,
        "reason": e.reason,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _user_block_to_dict(e: UserBlockList) -> dict:
    return {
        "id": str(e.id), "user_identifier": e.user_identifier,
        "brand_id": str(e.brand_id) if e.brand_id else None,
        "blocked_by": str(e.blocked_by) if e.blocked_by else None,
        "reason": e.reason,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
