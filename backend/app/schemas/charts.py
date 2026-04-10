"""Chart data schemas — MV-070."""
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
