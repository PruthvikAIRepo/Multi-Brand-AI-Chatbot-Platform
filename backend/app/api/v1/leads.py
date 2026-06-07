from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.lead import LeadCreateRequest
from app.services import lead_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import ChannelType

router = APIRouter(prefix="/brands/{brand_id}/leads", tags=["Leads"])


@router.post("", response_model=dict)
async def create_lead(
    brand_id: UUID,
    request: LeadCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a lead (dedup by email). Requires leads.view permission."""
    await check_brand_permission(db, current_user, brand_id, "leads.view")
    lead = await lead_service.create_or_update_lead(db, brand_id, request.model_dump())
    return api_response(data=lead, message="Lead captured successfully")


@router.get("", response_model=dict)
async def list_leads(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: ChannelType | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leads with masked PII. Requires leads.view."""
    await check_brand_permission(db, current_user, brand_id, "leads.view")
    leads, total = await lead_service.list_leads(db, brand_id, page, per_page, channel, search)
    return paginated_response(data=leads, total=total, page=page, per_page=per_page)


@router.get("/export", response_class=StreamingResponse)
async def export_leads_csv(
    brand_id: UUID,
    channel: ChannelType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export leads as CSV file. Decrypts PII for export. Requires leads.export."""
    await check_brand_permission(db, current_user, brand_id, "leads.export")
    csv_content = await lead_service.export_leads_csv(db, brand_id, channel)
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_{brand_id}.csv"},
    )


@router.get("/{lead_id}", response_model=dict)
async def get_lead(
    brand_id: UUID,
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single lead with full (unmasked) PII. Requires leads.view."""
    await check_brand_permission(db, current_user, brand_id, "leads.view")
    lead = await lead_service.get_lead(db, brand_id, lead_id)
    return api_response(data=lead)


@router.delete("/{lead_id}", response_model=dict)
async def delete_lead(
    brand_id: UUID,
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR: Permanently delete a lead. Requires leads.delete."""
    await check_brand_permission(db, current_user, brand_id, "leads.delete")
    await lead_service.delete_lead(db, brand_id, lead_id)
    return api_response(message="Lead deleted permanently")
