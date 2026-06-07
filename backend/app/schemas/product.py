from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.enums import SkinType, SkinConcern


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    ingredients: list[str] = []
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    image_url: str | None = None
    category: str | None = Field(None, max_length=100)
    purchase_url: str | None = None
    is_in_stock: bool = True
    priority_score: int = Field(default=0, ge=0)
    skin_types: list[SkinType] = []
    concerns: list[SkinConcern] = []


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    ingredients: list[str] | None = None
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    image_url: str | None = None
    category: str | None = Field(None, max_length=100)
    purchase_url: str | None = None
    is_in_stock: bool | None = None
    priority_score: int | None = Field(None, ge=0)
    skin_types: list[SkinType] | None = None
    concerns: list[SkinConcern] | None = None


class ProductResponse(BaseModel):
    id: UUID
    brand_id: UUID
    name: str
    description: str
    ingredients: list[str]
    price: Decimal
    image_url: str | None
    category: str | None
    purchase_url: str | None
    is_in_stock: bool
    priority_score: int
    skin_types: list[str]
    concerns: list[str]
    embedding_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
