"""CRUD schemas for manually-created health entities (MV-053).

All Create schemas omit server-managed fields (member_id, document_id,
is_manual_entry, created_at, updated_at).
All Update schemas have every field optional for PATCH semantics.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Medication
# ---------------------------------------------------------------------------


class MedicationCreate(BaseModel):
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True


class MedicationUpdate(BaseModel):
    drug_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class MedicationResponse(BaseModel):
    medication_id: uuid.UUID
    member_id: uuid.UUID
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


# ---------------------------------------------------------------------------
# Lab Result
# ---------------------------------------------------------------------------


class LabResultCreate(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: str = "NORMAL"
    test_date: Optional[date] = None


class LabResultUpdate(BaseModel):
    test_name: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: Optional[str] = None
    test_date: Optional[date] = None


class LabResultResponse(BaseModel):
    result_id: uuid.UUID
    member_id: uuid.UUID
    test_name: str
    test_name_normalized: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: str
    test_date: Optional[date] = None
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------


class DiagnosisCreate(BaseModel):
    condition_name: str
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    status: str = "UNKNOWN"


class DiagnosisUpdate(BaseModel):
    condition_name: Optional[str] = None
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    status: Optional[str] = None


class DiagnosisResponse(BaseModel):
    diagnosis_id: uuid.UUID
    member_id: uuid.UUID
    condition_name: str
    condition_normalized: Optional[str] = None
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    status: str
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Allergy
# ---------------------------------------------------------------------------


class AllergyCreate(BaseModel):
    allergen_name: str
    reaction_type: Optional[str] = None
    severity: Optional[str] = None


class AllergyUpdate(BaseModel):
    allergen_name: Optional[str] = None
    reaction_type: Optional[str] = None
    severity: Optional[str] = None


class AllergyResponse(BaseModel):
    allergy_id: uuid.UUID
    member_id: uuid.UUID
    allergen_name: str
    reaction_type: Optional[str] = None
    severity: Optional[str] = None
    confidence_score: str
    is_manual_entry: bool
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Vital
# ---------------------------------------------------------------------------


class VitalCreate(BaseModel):
    vital_type: str
    value: float
    unit: Optional[str] = None
    recorded_date: Optional[date] = None


class VitalResponse(BaseModel):
    vital_id: str
    member_id: str
    vital_type: str
    value: float
    unit: Optional[str] = None
    recorded_date: Optional[date] = None
    confidence_score: str
    model_config = ConfigDict(from_attributes=True)
