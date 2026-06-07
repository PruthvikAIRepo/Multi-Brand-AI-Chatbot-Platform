from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.prompt import PromptDraftRequest, PromptPublishRequest, PromptDiffRequest
from app.services import prompt_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User

router = APIRouter(prefix="/brands/{brand_id}/prompt", tags=["Prompt Management"])


@router.get("", response_model=dict)
async def get_live_prompt(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current live prompt. Requires prompt.view."""
    await check_brand_permission(db, current_user, brand_id, "prompt.view")
    prompt = await prompt_service.get_live_prompt(db, brand_id)
    return api_response(data=prompt, message="Live prompt" if prompt else "No live prompt set")


@router.get("/draft", response_model=dict)
async def get_draft(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current draft. Requires prompt.view."""
    await check_brand_permission(db, current_user, brand_id, "prompt.view")
    draft = await prompt_service.get_draft(db, brand_id)
    return api_response(data=draft, message="Current draft" if draft else "No draft exists")


@router.put("/draft", response_model=dict)
async def save_draft(
    brand_id: UUID,
    request: PromptDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update draft. Does not affect the live prompt. Requires prompt.edit."""
    await check_brand_permission(db, current_user, brand_id, "prompt.edit")
    draft = await prompt_service.save_draft(
        db, brand_id, current_user.id, request.content, request.annotation
    )
    return api_response(data=draft, message="Draft saved")


@router.post("/publish", response_model=dict)
async def publish_draft(
    brand_id: UUID,
    request: PromptPublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish the current draft as live. Old live version is archived. Requires prompt.edit."""
    await check_brand_permission(db, current_user, brand_id, "prompt.edit")
    prompt = await prompt_service.publish_draft(db, brand_id, current_user.id, request.annotation)
    return api_response(data=prompt, message="Prompt published and is now live")


@router.get("/versions", response_model=dict)
async def list_versions(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List published prompt versions (history). Most recent first. Requires prompt.view."""
    await check_brand_permission(db, current_user, brand_id, "prompt.view")
    versions, total = await prompt_service.list_versions(db, brand_id, page, per_page)
    return paginated_response(data=versions, total=total, page=page, per_page=per_page)


@router.get("/versions/{version_number}", response_model=dict)
async def get_version(
    brand_id: UUID,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific version by number. Requires prompt.view."""
    await check_brand_permission(db, current_user, brand_id, "prompt.view")
    version = await prompt_service.get_version(db, brand_id, version_number)
    return api_response(data=version)


@router.post("/versions/{version_number}/restore", response_model=dict)
async def restore_version(
    brand_id: UUID,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore an old version as the new live prompt. Requires prompt.edit."""
    await check_brand_permission(db, current_user, brand_id, "prompt.edit")
    prompt = await prompt_service.restore_version(db, brand_id, version_number, current_user.id)
    return api_response(data=prompt, message=f"Version {version_number} restored as live")


@router.post("/diff", response_model=dict)
async def diff_versions(
    brand_id: UUID,
    request: PromptDiffRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare two versions side by side. Returns unified diff. Requires prompt.view."""
    await check_brand_permission(db, current_user, brand_id, "prompt.view")
    diff = await prompt_service.diff_versions(db, brand_id, request.version_a, request.version_b)
    return api_response(data=diff)
