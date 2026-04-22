"""Charts API — lab trend time-series + medication Gantt + vitals trend endpoints — MV-070, MV-072, MV-073."""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_vault_access
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.models.vital import Vital
from app.schemas.charts import (
    AvailableTestsResponse,
    LabDataPoint,
    LabTrendResponse,
    LabTrendSeries,
    MedicationBar,
    MedicationTimelineResponse,
    VitalDataPoint,
    VitalsTrendResponse,
    VitalsTrendSeries,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _load_member_or_404(
    db: DbSession,
    member_id: uuid.UUID,
    current_user,
) -> FamilyMember:
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == member_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )
    await require_vault_access(member_id, current_user, db)
    return member


def _build_reference_range(lab: LabResult) -> Optional[str]:
    """Build a human-readable reference range string from the most recent result."""
    if lab.reference_low is not None and lab.reference_high is not None:
        return f"{lab.reference_low}–{lab.reference_high}"
    if lab.reference_low is not None:
        return f"≥{lab.reference_low}"
    if lab.reference_high is not None:
        return f"≤{lab.reference_high}"
    return None


@router.get("/lab-trends", response_model=LabTrendResponse)
async def get_lab_trends(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    test_names: Optional[str] = None,
) -> LabTrendResponse:
    """Return time-series lab data grouped by test name for charting.

    Query params:
    - member_id: UUID of the family member (required)
    - test_names: comma-separated list of test names to filter (optional; omit for all)
    """
    member = await _load_member_or_404(db, member_id, current_user)

    rows = (
        await db.execute(
            select(LabResult)
            .where(
                LabResult.member_id == member.member_id,
                LabResult.test_date.is_not(None),
                LabResult.value.is_not(None),
            )
            .order_by(LabResult.test_date.asc())
        )
    ).scalars().all()

    # Build filter set from comma-separated query param (normalize for comparison)
    filter_keys: Optional[set] = None
    if test_names:
        filter_keys = {name.strip().lower() for name in test_names.split(",") if name.strip()}

    # Group by normalized test name (strip + lowercase) while preserving original casing
    # groups: normalized_key -> list of LabResult rows
    groups: Dict[str, List[LabResult]] = defaultdict(list)
    key_to_display: Dict[str, str] = {}  # normalized_key -> first-seen original test_name
    for row in rows:
        key = row.test_name.strip().lower()
        if filter_keys is not None and key not in filter_keys:
            continue
        groups[key].append(row)
        if key not in key_to_display:
            key_to_display[key] = row.test_name

    series: List[LabTrendSeries] = []
    for key, lab_rows in groups.items():
        data_points = [
            LabDataPoint(
                date=r.test_date,
                value=float(r.value),
                unit=r.unit,
                is_abnormal=(r.flag != "NORMAL") if r.flag is not None else None,
                document_id=str(r.document_id) if r.document_id is not None else None,
            )
            for r in lab_rows
        ]

        # Most recent result (last in ASC-ordered list)
        most_recent = lab_rows[-1]
        unit = most_recent.unit
        reference_range = _build_reference_range(most_recent)

        series.append(
            LabTrendSeries(
                test_name=key_to_display[key],
                unit=unit,
                data_points=data_points,
                has_enough_data=len(data_points) >= 2,
                reference_range=reference_range,
            )
        )

    logger.info(
        "Lab trend data retrieved",
        extra={
            "member_id": str(member.member_id),
            "user_id": str(current_user.user_id),
            "series_count": len(series),
        },
    )

    return LabTrendResponse(
        member_id=str(member.member_id),
        series=series,
    )


@router.get("/available-tests", response_model=AvailableTestsResponse)
async def get_available_tests(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AvailableTestsResponse:
    """Return distinct test names that have at least one result with a non-null test_date."""
    member = await _load_member_or_404(db, member_id, current_user)

    rows = (
        await db.execute(
            select(LabResult)
            .where(
                LabResult.member_id == member.member_id,
                LabResult.test_date.is_not(None),
            )
            .order_by(LabResult.test_date.asc())
        )
    ).scalars().all()

    # Collect distinct test names preserving first-seen original casing
    seen: set = set()
    distinct_names: List[str] = []
    for row in rows:
        key = row.test_name.strip().lower()
        if key not in seen:
            seen.add(key)
            distinct_names.append(row.test_name)

    logger.info(
        "Available tests retrieved",
        extra={
            "member_id": str(member.member_id),
            "user_id": str(current_user.user_id),
            "test_count": len(distinct_names),
        },
    )

    return AvailableTestsResponse(
        member_id=str(member.member_id),
        test_names=distinct_names,
    )


@router.get("/medication-timeline", response_model=MedicationTimelineResponse)
async def get_medication_timeline(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MedicationTimelineResponse:
    """Return medication timeline data for Gantt chart rendering.

    Query params:
    - member_id: UUID of the family member (required)

    Returns all medications with drug_name IS NOT NULL, sorted by start_day asc
    then drug_name asc.  Relative start_day and duration_days are pre-computed
    so the frontend can render bars without date arithmetic.
    """
    member = await _load_member_or_404(db, member_id, current_user)

    rows: List[Medication] = (
        await db.execute(
            select(Medication)
            .where(
                Medication.member_id == member.member_id,
                Medication.drug_name.is_not(None),
            )
        )
    ).scalars().all()

    today: date = date.today()

    # Determine earliest start date across all medications
    start_dates = [m.start_date for m in rows if m.start_date is not None]
    if start_dates:
        earliest_date: date = min(start_dates)
    else:
        earliest_date = today - timedelta(days=365)

    bars: List[MedicationBar] = []
    for med in rows:
        if med.start_date is not None:
            start_day = (med.start_date - earliest_date).days
        else:
            start_day = 0

        if med.end_date is not None and med.start_date is not None:
            duration_days: Optional[int] = (med.end_date - med.start_date).days
        else:
            duration_days = None

        bars.append(
            MedicationBar(
                medication_id=str(med.medication_id),
                drug_name=med.drug_name,
                dosage=med.dosage,
                is_active=med.is_active,
                start_date=med.start_date.isoformat() if med.start_date is not None else None,
                end_date=med.end_date.isoformat() if med.end_date is not None else None,
                start_day=start_day,
                duration_days=duration_days,
            )
        )

    # Sort by start_day asc, then drug_name asc
    bars.sort(key=lambda b: (b.start_day, b.drug_name))

    logger.info(
        "Medication timeline retrieved",
        extra={
            "member_id": str(member.member_id),
            "user_id": str(current_user.user_id),
            "count": len(bars),
        },
    )

    return MedicationTimelineResponse(
        bars=bars,
        member_id=str(member.member_id),
        earliest_date=earliest_date.isoformat() if start_dates else None,
        today=today.isoformat(),
    )


_VITAL_DISPLAY_NAMES: Dict[str, str] = {
    "blood_pressure": "Blood Pressure",
    "heart_rate": "Heart Rate",
    "weight": "Weight",
    "height": "Height",
    "temperature": "Temperature",
    "spo2": "SpO₂",
    "bmi": "BMI",
}


@router.get("/vitals-trends", response_model=VitalsTrendResponse)
async def get_vitals_trends(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> VitalsTrendResponse:
    """Return time-series vital data grouped by vital_type for charting.

    Query params:
    - member_id: UUID of the family member (required)
    """
    member = await _load_member_or_404(db, member_id, current_user)

    rows: List[Vital] = (
        await db.execute(
            select(Vital)
            .where(
                Vital.member_id == member.member_id,
                Vital.recorded_date.is_not(None),
            )
            .order_by(Vital.recorded_date.asc())
        )
    ).scalars().all()

    # Group by vital_type
    groups: Dict[str, List[Vital]] = defaultdict(list)
    for row in rows:
        groups[row.vital_type].append(row)

    series: List[VitalsTrendSeries] = []
    for vital_type, vital_rows in groups.items():
        data_points: List[VitalDataPoint] = []
        unit: Optional[str] = None

        for v in vital_rows:
            value_float = float(v.value)
            if v.unit is not None:
                unit = v.unit

            # For blood_pressure: systolic = value, diastolic = None
            # (The Numeric(8,2) column cannot store "120/80" strings;
            #  systolic is stored as the value directly.)
            if vital_type == "blood_pressure":
                systolic: Optional[float] = value_float
                diastolic: Optional[float] = None
            else:
                systolic = None
                diastolic = None

            data_points.append(
                VitalDataPoint(
                    recorded_at=v.recorded_date.isoformat() if v.recorded_date is not None else None,
                    value=value_float,
                    unit=v.unit,
                    vital_type=vital_type,
                    systolic=systolic,
                    diastolic=diastolic,
                )
            )

        display_name = _VITAL_DISPLAY_NAMES.get(vital_type, vital_type.replace("_", " ").title())

        series.append(
            VitalsTrendSeries(
                vital_type=vital_type,
                display_name=display_name,
                unit=unit,
                data_points=data_points,
                has_enough_data=len(data_points) >= 2,
            )
        )

    logger.info(
        "Vitals trend data retrieved",
        extra={
            "member_id": str(member.member_id),
            "user_id": str(current_user.user_id),
            "series_count": len(series),
        },
    )

    return VitalsTrendResponse(
        series=series,
        member_id=str(member.member_id),
    )
