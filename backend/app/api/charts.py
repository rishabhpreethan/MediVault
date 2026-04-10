"""Charts API — lab trend time-series endpoints — MV-070."""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.schemas.charts import (
    AvailableTestsResponse,
    LabDataPoint,
    LabTrendResponse,
    LabTrendSeries,
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
