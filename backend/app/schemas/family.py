"""Pydantic schemas for the family members API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FamilyMemberCreate(BaseModel):
    name: str
    date_of_birth: Optional[date] = None
    relationship: str
    blood_group: Optional[str] = None
    gender: Optional[str] = None


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    relationship: Optional[str] = None
    blood_group: Optional[str] = None
    gender: Optional[str] = None


class FamilyMemberResponse(BaseModel):
    member_id: str
    user_id: str
    name: str
    date_of_birth: Optional[date] = None
    relationship: str
    blood_group: Optional[str] = None
    gender: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
