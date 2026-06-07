from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import UserRole


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    must_change_password: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ADMIN
    brand_ids: list[UUID] = []
    permissions: list[str] | None = None  # None = all permissions (default)


class UpdateUserBrandsRequest(BaseModel):
    brand_ids: list[UUID]


class UpdateUserPermissionsRequest(BaseModel):
    permissions: list[str]
