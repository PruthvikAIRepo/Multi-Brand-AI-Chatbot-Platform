import difflib
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prompt_version import PromptVersion
from app.core.exceptions import NotFoundError, BadRequestError


async def get_live_prompt(db: AsyncSession, brand_id: UUID) -> dict | None:
    """Get the current live prompt for a brand."""
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_live == True,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        return None
    return _prompt_to_dict(prompt)


async def get_draft(db: AsyncSession, brand_id: UUID) -> dict | None:
    """Get the current draft for a brand."""
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_draft == True,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        return None
    return _prompt_to_dict(prompt)


async def save_draft(db: AsyncSession, brand_id: UUID, user_id: UUID, content: str, annotation: str | None) -> dict:
    """Save a draft prompt. Only one draft per brand — overwrites existing."""
    # Check for existing draft
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_draft == True,
        )
    )
    existing_draft = result.scalar_one_or_none()

    if existing_draft:
        existing_draft.content = content
        existing_draft.annotation = annotation
        existing_draft.created_by = user_id
        await db.flush()
        return _prompt_to_dict(existing_draft)

    # Get next version number
    next_version = await _get_next_version(db, brand_id)

    draft = PromptVersion(
        brand_id=brand_id,
        version_number=next_version,
        content=content,
        annotation=annotation,
        is_live=False,
        is_draft=True,
        created_by=user_id,
    )
    db.add(draft)
    await db.flush()
    return _prompt_to_dict(draft)


async def publish_draft(db: AsyncSession, brand_id: UUID, user_id: UUID, annotation: str | None) -> dict:
    """Publish the current draft as the live prompt. Old live version is archived."""
    # Get current draft
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_draft == True,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise BadRequestError("No draft to publish. Save a draft first.")

    # Archive current live version
    live_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_live == True,
        )
    )
    current_live = live_result.scalar_one_or_none()
    if current_live:
        current_live.is_live = False

    # Make draft live
    draft.is_live = True
    draft.is_draft = False
    draft.published_at = datetime.now(timezone.utc)
    if annotation:
        draft.annotation = annotation

    await db.flush()
    return _prompt_to_dict(draft)


async def list_versions(
    db: AsyncSession, brand_id: UUID, page: int = 1, per_page: int = 20
) -> tuple[list[dict], int]:
    """List prompt version history for a brand. Most recent first."""
    count_result = await db.execute(
        select(func.count()).select_from(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_draft == False,
        )
    )
    total = count_result.scalar()

    result = await db.execute(
        select(PromptVersion)
        .where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_draft == False,
        )
        .order_by(PromptVersion.version_number.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    versions = result.scalars().all()

    return [_prompt_to_dict(v) for v in versions], total


async def get_version(db: AsyncSession, brand_id: UUID, version_number: int) -> dict:
    """Get a specific version by version number."""
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.version_number == version_number,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise NotFoundError("Prompt version", str(version_number))
    return _prompt_to_dict(version)


async def restore_version(db: AsyncSession, brand_id: UUID, version_number: int, user_id: UUID) -> dict:
    """Restore an old version as the new live prompt. Current live is archived."""
    # Get the version to restore
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.version_number == version_number,
        )
    )
    old_version = result.scalar_one_or_none()
    if not old_version:
        raise NotFoundError("Prompt version", str(version_number))

    # Archive current live
    live_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.is_live == True,
        )
    )
    current_live = live_result.scalar_one_or_none()
    if current_live:
        current_live.is_live = False

    # Create a new version with the restored content
    next_version = await _get_next_version(db, brand_id)

    restored = PromptVersion(
        brand_id=brand_id,
        version_number=next_version,
        content=old_version.content,
        annotation=f"Restored from version {version_number}",
        is_live=True,
        is_draft=False,
        created_by=user_id,
        published_at=datetime.now(timezone.utc),
    )
    db.add(restored)
    await db.flush()
    return _prompt_to_dict(restored)


async def diff_versions(db: AsyncSession, brand_id: UUID, version_a: int, version_b: int) -> dict:
    """Get a diff between two versions. Returns line-by-line changes."""
    result_a = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.version_number == version_a,
        )
    )
    va = result_a.scalar_one_or_none()
    if not va:
        raise NotFoundError("Prompt version", str(version_a))

    result_b = await db.execute(
        select(PromptVersion).where(
            PromptVersion.brand_id == brand_id,
            PromptVersion.version_number == version_b,
        )
    )
    vb = result_b.scalar_one_or_none()
    if not vb:
        raise NotFoundError("Prompt version", str(version_b))

    # Generate unified diff
    lines_a = va.content.splitlines(keepends=True)
    lines_b = vb.content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        lines_a, lines_b,
        fromfile=f"Version {version_a}",
        tofile=f"Version {version_b}",
    ))

    return {
        "version_a": {"number": version_a, "annotation": va.annotation},
        "version_b": {"number": version_b, "annotation": vb.annotation},
        "diff": "".join(diff),
        "has_changes": len(diff) > 0,
    }


# --- Helpers ---

async def _get_next_version(db: AsyncSession, brand_id: UUID) -> int:
    result = await db.execute(
        select(func.max(PromptVersion.version_number)).where(
            PromptVersion.brand_id == brand_id
        )
    )
    max_version = result.scalar()
    return (max_version or 0) + 1


def _prompt_to_dict(prompt: PromptVersion) -> dict:
    return {
        "id": str(prompt.id),
        "brand_id": str(prompt.brand_id),
        "version_number": prompt.version_number,
        "content": prompt.content,
        "annotation": prompt.annotation,
        "is_live": prompt.is_live,
        "is_draft": prompt.is_draft,
        "created_by": str(prompt.created_by),
        "published_at": prompt.published_at.isoformat() if prompt.published_at else None,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
    }
