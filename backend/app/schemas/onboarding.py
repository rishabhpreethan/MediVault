from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class OnboardingRequest(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    role: str = "PATIENT"
    allergies: list[str] = []
    licence_number: Optional[str] = None
    registration_council: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("PATIENT", "PROVIDER"):
            raise ValueError("role must be PATIENT or PROVIDER")
        return v

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Unknown"}
        if v not in valid:
            raise ValueError(f"blood_group must be one of {valid}")
        return v


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    role: str


class OnboardingCompleteResponse(BaseModel):
    message: str
    role: str
    onboarding_completed: bool
