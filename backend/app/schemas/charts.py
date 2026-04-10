"""Chart data schemas — MV-070, MV-072, MV-073."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class LabDataPoint(BaseModel):
    date: date
    value: float
    unit: Optional[str] = None
    is_abnormal: Optional[bool] = None
    document_id: Optional[str] = None


class LabTrendSeries(BaseModel):
    test_name: str
    unit: Optional[str] = None
    data_points: List[LabDataPoint]
    has_enough_data: bool  # True if len(data_points) >= 2
    reference_range: Optional[str] = None  # from most recent result


class LabTrendResponse(BaseModel):
    member_id: str
    series: List[LabTrendSeries]  # one per distinct test_name
    model_config = ConfigDict(from_attributes=True)


class AvailableTestsResponse(BaseModel):
    member_id: str
    test_names: List[str]  # distinct test names that have >= 1 result with a date


# ── MV-072: Medication Gantt chart schemas ──────────────────────────────────


class MedicationBar(BaseModel):
    medication_id: str
    drug_name: str
    dosage: Optional[str] = None
    is_active: bool
    start_date: Optional[str] = None   # ISO date string or None
    end_date: Optional[str] = None     # ISO date string or None (None = ongoing)
    start_day: int                      # days from earliest start date (0-indexed)
    duration_days: Optional[int] = None  # None if ongoing (no end_date)


class MedicationTimelineResponse(BaseModel):
    bars: List[MedicationBar]
    member_id: str
    earliest_date: Optional[str] = None  # ISO date of earliest med start
    today: str                            # ISO date of today for ongoing bar length


# ── MV-073: Vitals trend chart schemas ─────────────────────────────────────


class VitalDataPoint(BaseModel):
    recorded_at: Optional[str] = None   # ISO date string or None
    value: float
    unit: Optional[str] = None
    vital_type: str
    systolic: Optional[float] = None    # for blood_pressure: same as value
    diastolic: Optional[float] = None   # for blood_pressure: not available from single Numeric column


class VitalsTrendSeries(BaseModel):
    vital_type: str
    display_name: str            # human-readable, e.g. "Blood Pressure"
    unit: Optional[str] = None
    data_points: List[VitalDataPoint]
    has_enough_data: bool        # >= 2 points


class VitalsTrendResponse(BaseModel):
    series: List[VitalsTrendSeries]
    member_id: str
