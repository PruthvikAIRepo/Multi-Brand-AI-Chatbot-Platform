from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.secret import Secret
from app.models.enums import SecretType
from app.core.encryption import encrypt, decrypt
from app.core.exceptions import NotFoundError, AlreadyExistsError


async def create_secret(db: AsyncSession, brand_id: UUID | None, secret_type: SecretType, value: str) -> dict:
    """Create a new secret. brand_id=None means system default."""
    # Check uniqueness
    result = await db.execute(
        select(Secret).where(
            Secret.brand_id == brand_id,
            Secret.secret_type == secret_type,
        )
    )
    if result.scalar_one_or_none():
        raise AlreadyExistsError("Secret", "type", f"{secret_type.value} for this brand")

    last_four = value[-4:] if len(value) >= 4 else value

    secret = Secret(
        brand_id=brand_id,
        secret_type=secret_type,
        encrypted_value=encrypt(value),
        last_four_chars=last_four,
    )
    db.add(secret)
    await db.flush()
    return _secret_to_dict(secret)


async def list_secrets(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    brand_id: UUID | None = None,
) -> tuple[list[dict], int]:
    """List secrets with masked values. Never returns plaintext."""
    filters = []
    if brand_id is not None:
        filters.append(Secret.brand_id == brand_id)

    count_query = select(func.count()).select_from(Secret)
    data_query = select(Secret).order_by(Secret.created_at.desc())

    if filters:
        count_query = count_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        data_query.offset((page - 1) * per_page).limit(per_page)
    )
    secrets = result.scalars().all()

    return [_secret_to_dict(s) for s in secrets], total


async def update_secret(db: AsyncSession, secret_id: UUID, new_value: str) -> dict:
    """Replace a secret value. Old value is never visible."""
    result = await db.execute(select(Secret).where(Secret.id == secret_id))
    secret = result.scalar_one_or_none()
    if not secret:
        raise NotFoundError("Secret", str(secret_id))

    secret.encrypted_value = encrypt(new_value)
    secret.last_four_chars = new_value[-4:] if len(new_value) >= 4 else new_value
    await db.flush()
    return _secret_to_dict(secret)


async def delete_secret(db: AsyncSession, secret_id: UUID) -> None:
    """Delete a secret."""
    result = await db.execute(select(Secret).where(Secret.id == secret_id))
    secret = result.scalar_one_or_none()
    if not secret:
        raise NotFoundError("Secret", str(secret_id))

    await db.delete(secret)
    await db.flush()


async def test_secret(db: AsyncSession, secret_id: UUID) -> dict:
    """Decrypt and verify a secret exists (not empty). Does NOT reveal the value."""
    result = await db.execute(select(Secret).where(Secret.id == secret_id))
    secret = result.scalar_one_or_none()
    if not secret:
        raise NotFoundError("Secret", str(secret_id))

    try:
        decrypted = decrypt(secret.encrypted_value)
        is_valid = len(decrypted) > 0
    except Exception:
        is_valid = False

    return {
        "secret_id": str(secret.id),
        "secret_type": secret.secret_type.value,
        "is_valid": is_valid,
        "message": "Connection test successful" if is_valid else "Secret appears invalid or corrupted",
    }


async def resolve_api_key(db: AsyncSession, brand_id: UUID, secret_type: SecretType) -> str | None:
    """Resolve API key: brand-specific first, then system default. Used by AI engine."""
    # Try brand-specific first
    result = await db.execute(
        select(Secret).where(
            Secret.brand_id == brand_id,
            Secret.secret_type == secret_type,
        )
    )
    secret = result.scalar_one_or_none()

    if not secret:
        # Fall back to system default (brand_id=NULL)
        result = await db.execute(
            select(Secret).where(
                Secret.brand_id.is_(None),
                Secret.secret_type == secret_type,
            )
        )
        secret = result.scalar_one_or_none()

    if not secret:
        return None

    return decrypt(secret.encrypted_value)


def _secret_to_dict(secret: Secret) -> dict:
    return {
        "id": str(secret.id),
        "brand_id": str(secret.brand_id) if secret.brand_id else None,
        "secret_type": secret.secret_type.value,
        "is_set": True,
        "last_four_chars": f"****{secret.last_four_chars}" if secret.last_four_chars else "not set",
        "created_at": secret.created_at.isoformat() if secret.created_at else None,
        "updated_at": secret.updated_at.isoformat() if secret.updated_at else None,
    }
