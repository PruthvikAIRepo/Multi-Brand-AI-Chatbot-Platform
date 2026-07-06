from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import ChatbotStatus


class BrandCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = None  # Auto-generated from name if not provided
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: str | None = None
    currency: str = Field(default="USD", max_length=3)


class BrandUpdateRequest(BaseModel):
    # Note: `is_active` is intentionally NOT here — activating/deactivating a brand
    # is a Super-Admin-only action (see /brands/{id}/activate|deactivate), because
    # deactivating a brand takes its chatbot offline (≈ soft-delete).
    model_config = {"extra": "forbid"}
    name: str | None = Field(None, min_length=1, max_length=255)
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: str | None = None
    currency: str | None = Field(None, max_length=3)


class BrandResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: str | None
    primary_color: str | None
    secondary_color: str | None
    accent_color: str | None
    description: str | None
    currency: str
    chatbot_status: ChatbotStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrandListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: str | None
    primary_color: str | None
    chatbot_status: ChatbotStatus
    is_active: bool
    product_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
