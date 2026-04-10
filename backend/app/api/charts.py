"""Charts API — lab trend time-series + medication Gantt endpoints — MV-070, MV-072."""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.schemas.charts import (
    AvailableTestsResponse,
    LabDataPoint,
    LabTrendResponse,
    LabTrendSeries,
    MedicationBar,
    MedicationTimelineResponse,
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
    require_member_access(member.user_id, current_user)
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
