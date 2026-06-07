from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import Product, ProductSkinType, ProductConcern
from app.models.embedding import EmbeddingSyncStatus
from app.models.enums import SkinType, SkinConcern, EntityType, EmbeddingStatus
from app.core.exceptions import NotFoundError


async def create_product(db: AsyncSession, brand_id: UUID, data: dict) -> dict:
    """Create a product with skin types, concerns, and trigger embedding sync."""
    product = Product(
        brand_id=brand_id,
        name=data["name"],
        description=data["description"],
        ingredients=data.get("ingredients", []),
        price=data["price"],
        image_url=data.get("image_url"),
        category=data.get("category"),
        purchase_url=data.get("purchase_url"),
        is_in_stock=data.get("is_in_stock", True),
        priority_score=data.get("priority_score", 0),
    )
    db.add(product)
    await db.flush()

    # Add skin types
    for st in set(data.get("skin_types", [])):
        db.add(ProductSkinType(product_id=product.id, skin_type=st))

    # Add concerns
    for concern in set(data.get("concerns", [])):
        db.add(ProductConcern(product_id=product.id, concern=concern))

    # Create embedding sync status (pending — Celery worker will process)
    db.add(EmbeddingSyncStatus(
        brand_id=brand_id,
        entity_type=EntityType.PRODUCT,
        entity_id=product.id,
        status=EmbeddingStatus.PENDING,
    ))

    await db.flush()

    return await _load_product_response(db, product.id)


async def list_products(
    db: AsyncSession,
    brand_id: UUID,
    page: int = 1,
    per_page: int = 20,
    category: str | None = None,
    skin_type: SkinType | None = None,
    concern: SkinConcern | None = None,
    in_stock: bool | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    """List products for a brand with filters and pagination. Excludes soft-deleted."""
    # Base query — only non-deleted products for this brand
    base_filter = [
        Product.brand_id == brand_id,
        Product.deleted_at.is_(None),
    ]

    if category:
        base_filter.append(Product.category == category)
    if in_stock is not None:
        base_filter.append(Product.is_in_stock == in_stock)
    if search:
        base_filter.append(Product.name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(Product).where(*base_filter)

    # Apply skin_type / concern filters via subqueries
    if skin_type:
        count_query = count_query.where(
            Product.id.in_(
                select(ProductSkinType.product_id).where(ProductSkinType.skin_type == skin_type)
            )
        )
    if concern:
        count_query = count_query.where(
            Product.id.in_(
                select(ProductConcern.product_id).where(ProductConcern.concern == concern)
            )
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Fetch products
    query = (
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(*base_filter)
        .order_by(Product.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    if skin_type:
        query = query.where(
            Product.id.in_(
                select(ProductSkinType.product_id).where(ProductSkinType.skin_type == skin_type)
            )
        )
    if concern:
        query = query.where(
            Product.id.in_(
                select(ProductConcern.product_id).where(ProductConcern.concern == concern)
            )
        )

    result = await db.execute(query)
    products = result.scalars().unique().all()

    # Get embedding statuses in one query
    product_ids = [p.id for p in products]
    embed_statuses = await _get_embedding_statuses(db, product_ids)

    data = [_product_to_dict(p, embed_statuses.get(p.id)) for p in products]
    return data, total


async def get_product(db: AsyncSession, brand_id: UUID, product_id: UUID) -> dict:
    """Get a single product with skin types, concerns, and embedding status."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(
            Product.id == product_id,
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product", str(product_id))

    embed_statuses = await _get_embedding_statuses(db, [product.id])
    return _product_to_dict(product, embed_statuses.get(product.id))


async def update_product(db: AsyncSession, brand_id: UUID, product_id: UUID, data: dict) -> dict:
    """Update product. Re-triggers embedding if text content changes."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(
            Product.id == product_id,
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product", str(product_id))

    # Track if text content changes (needs re-embedding)
    text_changed = False

    # Update scalar fields
    for field in ["name", "description", "ingredients", "price", "image_url", "category", "purchase_url", "is_in_stock", "priority_score"]:
        if field in data:
            if field in ("name", "description", "ingredients") and getattr(product, field) != data[field]:
                text_changed = True
            setattr(product, field, data[field])

    # Update skin types if provided
    if "skin_types" in data:
        # Remove existing
        for st in product.skin_types:
            await db.delete(st)
        # Add new
        for st in set(data["skin_types"]):
            db.add(ProductSkinType(product_id=product.id, skin_type=st))

    # Update concerns if provided
    if "concerns" in data:
        for c in product.concerns:
            await db.delete(c)
        for concern in set(data["concerns"]):
            db.add(ProductConcern(product_id=product.id, concern=concern))

    # Re-trigger embedding if text content changed
    if text_changed:
        await _update_embedding_status(db, brand_id, product.id, EmbeddingStatus.PENDING)

    await db.flush()

    return await _load_product_response(db, product.id)


async def delete_product(db: AsyncSession, brand_id: UUID, product_id: UUID) -> None:
    """Soft delete a product. Sets deleted_at timestamp."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.brand_id == brand_id,
            Product.deleted_at.is_(None),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product", str(product_id))

    product.deleted_at = datetime.now(timezone.utc)

    # Remove embedding sync status and embeddings for this product
    embed_result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.entity_type == EntityType.PRODUCT,
            EmbeddingSyncStatus.entity_id == product_id,
        )
    )
    for status in embed_result.scalars().all():
        await db.delete(status)

    await db.flush()


# --- Helpers ---

async def _load_product_response(db: AsyncSession, product_id: UUID) -> dict:
    """Load a product with all relationships for response."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.skin_types), selectinload(Product.concerns))
        .where(Product.id == product_id)
    )
    product = result.scalar_one()
    embed_statuses = await _get_embedding_statuses(db, [product.id])
    return _product_to_dict(product, embed_statuses.get(product.id))


async def _get_embedding_statuses(db: AsyncSession, product_ids: list[UUID]) -> dict[UUID, str]:
    """Get embedding statuses for multiple products in one query."""
    if not product_ids:
        return {}
    result = await db.execute(
        select(EmbeddingSyncStatus.entity_id, EmbeddingSyncStatus.status).where(
            EmbeddingSyncStatus.entity_type == EntityType.PRODUCT,
            EmbeddingSyncStatus.entity_id.in_(product_ids),
        )
    )
    return {row.entity_id: row.status.value for row in result.all()}


async def _update_embedding_status(
    db: AsyncSession, brand_id: UUID, product_id: UUID, status: EmbeddingStatus
) -> None:
    """Update or create embedding sync status for a product."""
    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.entity_type == EntityType.PRODUCT,
            EmbeddingSyncStatus.entity_id == product_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = status
        existing.error_message = None
    else:
        db.add(EmbeddingSyncStatus(
            brand_id=brand_id,
            entity_type=EntityType.PRODUCT,
            entity_id=product_id,
            status=status,
        ))


def _product_to_dict(product: Product, embedding_status: str | None = None) -> dict:
    return {
        "id": str(product.id),
        "brand_id": str(product.brand_id),
        "name": product.name,
        "description": product.description,
        "ingredients": product.ingredients or [],
        "price": str(product.price),
        "image_url": product.image_url,
        "category": product.category,
        "purchase_url": product.purchase_url,
        "is_in_stock": product.is_in_stock,
        "priority_score": product.priority_score,
        "skin_types": [st.skin_type.value for st in product.skin_types],
        "concerns": [c.concern.value for c in product.concerns],
        "embedding_status": embedding_status,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }
