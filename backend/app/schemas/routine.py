from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import SkinType, SkinConcern, RoutineStepName


class RoutineStepRequest(BaseModel):
    step_number: int = Field(..., ge=1)
    step_name: RoutineStepName
    product_id: UUID
    instructions: str | None = None


class RoutineCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_skin_type: SkinType | None = None
    target_concerns: list[str] = []
    steps: list[RoutineStepRequest] = []


class RoutineUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target_skin_type: SkinType | None = None
    target_concerns: list[str] | None = None
    is_active: bool | None = None
    steps: list[RoutineStepRequest] | None = None
