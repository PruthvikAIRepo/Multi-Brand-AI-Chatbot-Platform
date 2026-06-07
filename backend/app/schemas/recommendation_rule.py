from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import RecommendationRuleType, SkinType, SkinConcern


class RecommendationRuleCreateRequest(BaseModel):
    rule_type: RecommendationRuleType
    config: dict
    description: str | None = None
    is_active: bool = True


class RecommendationRuleUpdateRequest(BaseModel):
    rule_type: RecommendationRuleType | None = None
    config: dict | None = None
    description: str | None = None
    is_active: bool | None = None


class RuleTestRequest(BaseModel):
    skin_type: SkinType
    concerns: list[SkinConcern] = []
    preferences: list[str] = []
