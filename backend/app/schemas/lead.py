from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.models.enums import ChannelType


class LeadCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = None
    channel: ChannelType
    consent: bool = True
    consent_text: str | None = None
    conversation_id: UUID | None = None
