from pydantic import BaseModel, Field
from uuid import UUID


class PromptDraftRequest(BaseModel):
    content: str = Field(..., min_length=1)
    annotation: str | None = None


class PromptPublishRequest(BaseModel):
    annotation: str | None = None


class PromptDiffRequest(BaseModel):
    version_a: int = Field(..., ge=1)
    version_b: int = Field(..., ge=1)
