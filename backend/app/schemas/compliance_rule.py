from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import ComplianceRuleType


class ComplianceRuleCreateRequest(BaseModel):
    rule_type: ComplianceRuleType
    value: str = Field(..., min_length=1)
    is_active: bool = True


class ComplianceRuleUpdateRequest(BaseModel):
    rule_type: ComplianceRuleType | None = None
    value: str | None = Field(None, min_length=1)
    is_active: bool | None = None
