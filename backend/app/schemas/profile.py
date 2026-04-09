"""Profile response schemas — MV-051."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FamilyMemberSchema(BaseModel):
    member_id: str
    user_id: str
    full_name: str
    relationship: str
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    is_self: bool
    model_config = ConfigDict(from_attributes=True)


class MedicationSchema(BaseModel):
    medication_id: str
    drug_name: str
    drug_name_normalized: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


class LabResultSchema(BaseModel):
    result_id: str
    test_name: str
    test_name_normalized: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: str = "NORMAL"
    test_date: Optional[date] = None
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


class DiagnosisSchema(BaseModel):
    diagnosis_id: str
    condition_name: str
    condition_normalized: Optional[str] = None
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    status: str
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


class AllergySchema(BaseModel):
    allergy_id: str
    allergen_name: str
    reaction_type: Optional[str] = None
    severity: Optional[str] = None
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


class VitalSchema(BaseModel):
    vital_id: str
    vital_type: str
    value: float
    unit: Optional[str] = None
    recorded_date: Optional[date] = None
    confidence_score: str
    model_config = ConfigDict(from_attributes=True)


class HealthProfileResponse(BaseModel):
    member: FamilyMemberSchema
    medications: list[MedicationSchema]
    diagnoses: list[DiagnosisSchema]
    allergies: list[AllergySchema]
    recent_labs: list[LabResultSchema]
    recent_vitals: list[VitalSchema]


class ProfileSummaryResponse(BaseModel):
    member_id: str
    total_medications: int
    total_lab_results: int
    total_diagnoses: int
    low_confidence_count: int
