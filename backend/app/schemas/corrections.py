from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime


class FieldCorrectionRequest(BaseModel):
    field_name: str
    new_value: str


class CorrectionAuditResponse(BaseModel):
    audit_id: str
    entity_type: str
    entity_id: str
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    corrected_at: datetime

    model_config = ConfigDict(from_attributes=True)
