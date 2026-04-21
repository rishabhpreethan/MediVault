"""Provider / Doctor Workflow schemas — MV-156, MV-157."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Patient lookup / access request
# ---------------------------------------------------------------------------

class PatientLookupRequest(BaseModel):
    passport_id: UUID


class AccessRequestResponse(BaseModel):
    request_id: UUID
    provider_user_id: UUID
    patient_member_id: UUID
    passport_id_used: Optional[UUID] = None
    status: str
    requested_at: datetime
    responded_at: Optional[datetime] = None
    expires_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RespondToRequestBody(BaseModel):
    action: str  # "accept" | "decline"


class PatientLookupResponse(BaseModel):
    request_id: UUID
    status: str
    patient_name: Optional[str] = None
    message: str


class AccessRequestStatusResponse(BaseModel):
    request_id: UUID
    status: str
    responded_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Patient data (accessible after ACCEPTED request)
# ---------------------------------------------------------------------------

class PatientSummary(BaseModel):
    member_id: UUID
    full_name: str
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None


class EncounterResponse(BaseModel):
    encounter_id: UUID
    provider_user_id: UUID
    patient_member_id: UUID
    access_request_id: Optional[UUID] = None
    encounter_date: date
    chief_complaint: Optional[str] = None
    diagnosis_notes: Optional[str] = None
    prescriptions_note: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LogEncounterRequest(BaseModel):
    request_id: UUID
    encounter_date: date
    chief_complaint: Optional[str] = None
    diagnosis_notes: Optional[str] = None
    prescriptions_note: Optional[str] = None
    follow_up_date: Optional[date] = None


class PatientDataResponse(BaseModel):
    request_id: UUID
    patient: PatientSummary
    encounters: list[EncounterResponse]
