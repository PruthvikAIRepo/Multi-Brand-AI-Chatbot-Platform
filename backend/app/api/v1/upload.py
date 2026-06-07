"""File upload endpoint for product images and brand logos."""

from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import s3_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response
from app.core.exceptions import BadRequestError
from app.models.user import User

router = APIRouter(prefix="/brands/{brand_id}/upload", tags=["File Upload"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/product-image", response_model=dict)
async def upload_product_image(
    brand_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a product image. Returns the S3 URL. Requires products.edit."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    return await _upload_file(file, brand_id, "products")


@router.post("/brand-logo", response_model=dict)
async def upload_brand_logo(
    brand_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a brand logo. Returns the S3 URL. Requires brand.edit."""
    await check_brand_permission(db, current_user, brand_id, "brand.edit")
    return await _upload_file(file, brand_id, "logos")


@router.post("/asset", response_model=dict)
async def upload_brand_asset(
    brand_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a general brand asset. Returns the S3 URL. Requires brand.edit."""
    await check_brand_permission(db, current_user, brand_id, "brand.edit")
    return await _upload_file(file, brand_id, "assets")


async def _upload_file(file: UploadFile, brand_id: UUID, folder: str) -> dict:
    """Validate and upload a file to S3."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestError(f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")

    url = s3_service.upload_file(
        file_content=content,
        brand_id=brand_id,
        folder=folder,
        original_filename=file.filename or "upload.jpg",
        content_type=file.content_type,
    )

    return api_response(data={"url": url, "filename": file.filename, "size": len(content)}, message="File uploaded")
