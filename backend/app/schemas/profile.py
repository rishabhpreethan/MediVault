"""Profile response schemas — MV-051."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MedicationSchema(BaseModel):
    medication_id: str
    member_id: str
    document_id: Optional[str] = None
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    confidence_score: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class LabResultSchema(BaseModel):
    lab_result_id: str
    member_id: str
    document_id: Optional[str] = None
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: Optional[bool] = None
    confidence_score: str
    test_date: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)


class DiagnosisSchema(BaseModel):
    diagnosis_id: str
    member_id: str
    document_id: Optional[str] = None
    condition_name: str
    confidence_score: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class HealthProfileResponse(BaseModel):
    member_id: str
    medications: list[MedicationSchema]
    lab_results: list[LabResultSchema]
    diagnoses: list[DiagnosisSchema]


class ProfileSummaryResponse(BaseModel):
    member_id: str
    total_medications: int
    total_lab_results: int
    total_diagnoses: int
    low_confidence_count: int
