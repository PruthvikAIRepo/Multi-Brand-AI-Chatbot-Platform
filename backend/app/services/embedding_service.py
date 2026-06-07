"""Provider-agnostic embedding service. Generates and stores vector embeddings.
Supports OpenAI and Voyage AI. Switch via EMBEDDINGS_PROVIDER in .env."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.embedding import Embedding, EmbeddingSyncStatus
from app.models.product import Product
from app.models.faq import FAQ
from app.models.routine import Routine
from app.models.enums import EntityType, EmbeddingStatus
from app.config import get_settings

settings = get_settings()


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for a text string."""
    if settings.EMBEDDINGS_PROVIDER == "openai":
        return await _openai_embed(text)
    elif settings.EMBEDDINGS_PROVIDER == "voyage":
        return await _voyage_embed(text)
    else:
        raise ValueError(f"Unknown embeddings provider: {settings.EMBEDDINGS_PROVIDER}")


async def embed_entity(db: AsyncSession, brand_id: UUID, entity_type: EntityType, entity_id: UUID) -> None:
    """Generate embedding for a product/FAQ/routine and store in pgvector."""
    # Get the text content to embed
    text = await _get_entity_text(db, entity_type, entity_id)
    if not text:
        await _update_status(db, entity_type, entity_id, EmbeddingStatus.FAILED, "No text content found")
        return

    try:
        # Generate embedding vector
        vector = await generate_embedding(text)

        # Remove old embedding if exists
        old = await db.execute(
            select(Embedding).where(
                Embedding.brand_id == brand_id,
                Embedding.entity_type == entity_type,
                Embedding.entity_id == entity_id,
            )
        )
        for e in old.scalars().all():
            await db.delete(e)

        # Store new embedding
        db.add(Embedding(
            brand_id=brand_id,
            entity_type=entity_type,
            entity_id=entity_id,
            content=text,
            embedding=vector,
        ))

        # Update status
        await _update_status(db, entity_type, entity_id, EmbeddingStatus.COMPLETED)
        await db.flush()

    except Exception as e:
        await _update_status(db, entity_type, entity_id, EmbeddingStatus.FAILED, str(e))
        await db.flush()
        raise


async def search_similar(db: AsyncSession, brand_id: UUID, query: str, top_k: int = 5, threshold: float = 0.7) -> list[dict]:
    """Search for similar content in a brand's knowledge base using vector similarity."""
    query_vector = await generate_embedding(query)

    # Fetch all embeddings for this brand and compute similarity in Python
    # (pgvector cosine_distance has async greenlet issues with asyncpg)
    result = await db.execute(
        select(Embedding).where(Embedding.brand_id == brand_id)
    )
    embeddings = result.scalars().all()

    # Compute cosine similarity in Python
    import numpy as np
    q_vec = np.array(query_vector, dtype=np.float32)
    q_norm = np.linalg.norm(q_vec)

    scored = []
    for emb in embeddings:
        emb_vec = np.array(list(emb.embedding), dtype=np.float32)
        emb_norm = np.linalg.norm(emb_vec)
        if q_norm > 0 and emb_norm > 0:
            similarity = float(np.dot(emb_vec, q_vec) / (emb_norm * q_norm))
        else:
            similarity = 0.0
        if similarity >= threshold:
            scored.append((emb, similarity))

    # Sort by similarity descending, take top_k
    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:top_k]

    return [
        {
            "entity_type": emb.entity_type.value,
            "entity_id": str(emb.entity_id),
            "content": emb.content,
            "similarity": round(sim, 4),
        }
        for emb, sim in scored
    ]


# --- Provider implementations ---

async def _openai_embed(text: str) -> list[float]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.embeddings.create(
        model=settings.EMBEDDINGS_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def _voyage_embed(text: str) -> list[float]:
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.EMBEDDINGS_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.EMBEDDINGS_MODEL,
                "input": [text],
            },
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


# --- Helpers ---

async def _get_entity_text(db: AsyncSession, entity_type: EntityType, entity_id: UUID) -> str | None:
    """Get the text content of a product/FAQ/routine for embedding."""
    if entity_type == EntityType.PRODUCT:
        result = await db.execute(select(Product).where(Product.id == entity_id))
        product = result.scalar_one_or_none()
        if not product:
            return None
        ingredients = ", ".join(product.ingredients or [])
        return f"{product.name}. {product.description}. Ingredients: {ingredients}. Category: {product.category or 'General'}."

    elif entity_type == EntityType.FAQ:
        result = await db.execute(select(FAQ).where(FAQ.id == entity_id))
        faq = result.scalar_one_or_none()
        if not faq:
            return None
        return f"Q: {faq.question} A: {faq.answer}"

    elif entity_type == EntityType.ROUTINE:
        result = await db.execute(select(Routine).where(Routine.id == entity_id))
        routine = result.scalar_one_or_none()
        if not routine:
            return None
        return f"{routine.name}. {routine.description or ''}. For {routine.target_skin_type.value if routine.target_skin_type else 'all'} skin."

    return None


async def _update_status(db: AsyncSession, entity_type: EntityType, entity_id: UUID, status: EmbeddingStatus, error: str = None):
    result = await db.execute(
        select(EmbeddingSyncStatus).where(
            EmbeddingSyncStatus.entity_type == entity_type,
            EmbeddingSyncStatus.entity_id == entity_id,
        )
    )
    sync = result.scalar_one_or_none()
    if sync:
        sync.status = status
        sync.error_message = error
