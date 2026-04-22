"""Timeline API schemas — MV-060."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, ConfigDict


class TimelineEvent(BaseModel):
    event_id: str           # "{type}:{uuid}" e.g. "medication:abc-123"
    event_type: str         # "MEDICATION" | "LAB_RESULT" | "DIAGNOSIS" | "ALLERGY" | "VITAL" | "DOCUMENT" | "VISIT"
    event_date: Optional[date]
    title: str              # human-readable summary
    subtitle: Optional[str]  # secondary info (e.g. value + unit for labs, dosage for meds)
    source_document_id: Optional[str]
    confidence_score: Optional[str]
    metadata: Optional[Dict[str, Any]] = None  # VISIT: {encounter_id, diagnosis_notes, prescriptions_note, follow_up_date}
    model_config = ConfigDict(from_attributes=True)


class TimelineResponse(BaseModel):
    items: List[TimelineEvent]
    total: int
    page: int
    page_size: int
    member_id: str
