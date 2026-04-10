from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PassportCreate(BaseModel):
    member_id: str
    expires_in_days: int = 30          # 1–365
    show_medications: bool = True
    show_labs: bool = True
    show_diagnoses: bool = True
    show_allergies: bool = True


class PassportResponse(BaseModel):
    passport_id: str
    member_id: str
    share_token: str                    # UUID used in public URL (same as passport_id)
    expires_at: Optional[datetime]
    is_active: bool
    show_medications: bool
    show_labs: bool
    show_diagnoses: bool
    show_allergies: bool
    created_at: Optional[datetime]
    access_count: int
    model_config = ConfigDict(from_attributes=True)


class PassportListResponse(BaseModel):
    items: List[PassportResponse]
    total: int


class PublicPassportResponse(BaseModel):
    """Read-only public view — no auth required."""
    passport_id: str
    member_name: str                    # first name only for privacy
    blood_group: Optional[str]
    allergies: List[str]                # allergen names if show_allergies
    medications: List[dict]             # drug+dosage if show_medications
    diagnoses: List[str]                # condition names if show_diagnoses
    generated_at: datetime
    expires_at: Optional[datetime]
    disclaimer: str = "This information is patient-reported and for reference only."
