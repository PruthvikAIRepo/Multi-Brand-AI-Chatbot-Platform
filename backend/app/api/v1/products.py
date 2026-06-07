from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.services import product_service, audit_service
from app.core.permissions import get_current_user, check_brand_permission
from app.core.response import api_response, paginated_response
from app.models.user import User
from app.models.enums import SkinType, SkinConcern, EmbeddingStatus, AdminActionType

router = APIRouter(prefix="/brands/{brand_id}/products", tags=["Products"])


@router.post("", response_model=dict)
async def create_product(
    brand_id: UUID,
    request: ProductCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a product for a brand. Requires products.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    product = await product_service.create_product(db, brand_id, request.model_dump())
    await audit_service.log_action(
        db, current_user.id, AdminActionType.CREATED, "product",
        entity_name=product["name"], brand_id=brand_id, after_state=product,
    )
    return api_response(data=product, message="Product created successfully")


@router.get("", response_model=dict)
async def list_products(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    skin_type: SkinType | None = None,
    concern: SkinConcern | None = None,
    in_stock: bool | None = None,
    search: str | None = None,
    embedding_status: EmbeddingStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active products for a brand with filters. Requires products.view permission."""
    await check_brand_permission(db, current_user, brand_id, "products.view")
    products, total = await product_service.list_products(
        db, brand_id, page, per_page, category, skin_type, concern, in_stock, search,
        embedding_status=embedding_status,
    )
    return paginated_response(data=products, total=total, page=page, per_page=per_page)


@router.get("/deleted", response_model=dict)
async def list_deleted_products(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List soft-deleted products for review/restore. Requires products.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    products, total = await product_service.list_products(
        db, brand_id, page, per_page, deleted_only=True
    )
    return paginated_response(data=products, total=total, page=page, per_page=per_page)


@router.get("/{product_id}", response_model=dict)
async def get_product(
    brand_id: UUID,
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single product. Requires products.view permission."""
    await check_brand_permission(db, current_user, brand_id, "products.view")
    product = await product_service.get_product(db, brand_id, product_id)
    return api_response(data=product)


@router.put("/{product_id}", response_model=dict)
async def update_product(
    brand_id: UUID,
    product_id: UUID,
    request: ProductUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a product. Re-triggers embedding if text changes. Requires products.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    product = await product_service.update_product(
        db, brand_id, product_id, request.model_dump(exclude_unset=True)
    )
    return api_response(data=product, message="Product updated successfully")


@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    brand_id: UUID,
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a product. Removes from RAG search immediately. Requires products.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    await product_service.delete_product(db, brand_id, product_id)
    await audit_service.log_action(
        db, current_user.id, AdminActionType.DELETED, "product",
        entity_id=product_id, brand_id=brand_id,
    )
    return api_response(message="Product deleted successfully")


@router.post("/{product_id}/restore", response_model=dict)
async def restore_product(
    brand_id: UUID,
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted product. Re-triggers embedding. Requires products.edit permission."""
    await check_brand_permission(db, current_user, brand_id, "products.edit")
    product = await product_service.restore_product(db, brand_id, product_id)
    return api_response(data=product, message="Product restored successfully")
