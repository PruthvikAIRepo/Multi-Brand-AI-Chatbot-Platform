from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.faq import FAQCreateRequest, FAQUpdateRequest
from app.services import faq_service, audit_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import AdminActionType

router = APIRouter(prefix="/brands/{brand_id}/faqs", tags=["FAQs"])


@router.post("", response_model=dict)
async def create_faq(
    brand_id: UUID,
    request: FAQCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a FAQ. Triggers embedding. Requires faqs.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.edit")
    faq = await faq_service.create_faq(db, brand_id, request.model_dump())
    await audit_service.log_action(
        db, current_user.id, AdminActionType.CREATED, "faq",
        entity_id=faq.get("id"), brand_id=brand_id, entity_name=faq.get("question"),
    )
    return api_response(data=faq, message="FAQ created successfully")


@router.get("", response_model=dict)
async def list_faqs(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List FAQs with filters. Requires faqs.view permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.view")
    faqs, total = await faq_service.list_faqs(db, brand_id, page, per_page, category, search)
    return paginated_response(data=faqs, total=total, page=page, per_page=per_page)


@router.get("/deleted", response_model=dict)
async def list_deleted_faqs(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List soft-deleted FAQs for review/restore. Requires faqs.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.edit")
    faqs, total = await faq_service.list_faqs(db, brand_id, page, per_page, deleted_only=True)
    return paginated_response(data=faqs, total=total, page=page, per_page=per_page)


@router.get("/{faq_id}", response_model=dict)
async def get_faq(
    brand_id: UUID,
    faq_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single FAQ. Requires faqs.view permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.view")
    faq = await faq_service.get_faq(db, brand_id, faq_id)
    return api_response(data=faq)


@router.put("/{faq_id}", response_model=dict)
async def update_faq(
    brand_id: UUID,
    faq_id: UUID,
    request: FAQUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a FAQ. Re-triggers embedding if text changes. Requires faqs.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.edit")
    faq = await faq_service.update_faq(db, brand_id, faq_id, request.model_dump(exclude_unset=True))
    await audit_service.log_action(
        db, current_user.id, AdminActionType.UPDATED, "faq",
        entity_id=faq_id, brand_id=brand_id, entity_name=faq.get("question"),
    )
    return api_response(data=faq, message="FAQ updated successfully")


@router.delete("/{faq_id}", response_model=dict)
async def delete_faq(
    brand_id: UUID,
    faq_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a FAQ. Removes from RAG search. Requires faqs.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.edit")
    await faq_service.delete_faq(db, brand_id, faq_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.DELETED, "faq",
        entity_id=faq_id, brand_id=brand_id,
    )
    return api_response(message="FAQ deleted successfully")


@router.post("/{faq_id}/restore", response_model=dict)
async def restore_faq(
    brand_id: UUID,
    faq_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted FAQ. Re-triggers embedding. Requires faqs.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "faqs.edit")
    faq = await faq_service.restore_faq(db, brand_id, faq_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.RESTORED, "faq",
        entity_id=faq_id, brand_id=brand_id, entity_name=faq.get("question"),
    )
    return api_response(data=faq, message="FAQ restored successfully")
