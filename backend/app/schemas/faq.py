from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class FAQCreateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    category: str | None = Field(None, max_length=100)


class FAQUpdateRequest(BaseModel):
    question: str | None = Field(None, min_length=1)
    answer: str | None = Field(None, min_length=1)
    category: str | None = Field(None, max_length=100)


class FAQResponse(BaseModel):
    id: UUID
    brand_id: UUID
    question: str
    answer: str
    category: str | None
    embedding_status: str | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
