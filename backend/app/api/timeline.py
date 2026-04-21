"""Timeline API — paginated, filterable health event timeline (MV-060)."""
from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.document import Document
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medical_encounter import MedicalEncounter
from app.models.medication import Medication
from app.models.vital import Vital
from app.schemas.timeline import TimelineEvent, TimelineResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_VALID_EVENT_TYPES = {"MEDICATION", "LAB_RESULT", "DIAGNOSIS", "ALLERGY", "VITAL", "DOCUMENT", "VISIT"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_member_or_404(
    db: AsyncSession,
    member_id: uuid.UUID,
    current_user,
) -> FamilyMember:
    """Load a FamilyMember and verify ownership, or raise 404 / 403."""
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


def _parse_date(value: Optional[str], param_name: str) -> Optional[date]:
    """Parse an ISO date string (YYYY-MM-DD) or raise 400."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format for {param_name}. Expected YYYY-MM-DD.",
        )


async def _fetch_medications(
    db: AsyncSession,
    member_id: uuid.UUID,
) -> List[TimelineEvent]:
    """Fetch all Medication rows and convert to TimelineEvent list."""
    result = await db.execute(
        select(Medication).where(Medication.member_id == member_id)
    )
    rows = result.scalars().all()
    events = []
    for row in rows:
        subtitle_parts = [p for p in [row.dosage, row.frequency] if p]
        events.append(
            TimelineEvent(
                event_id=f"medication:{row.medication_id}",
                event_type="MEDICATION",
                event_date=None,
                title=row.drug_name,
                subtitle=" ".join(subtitle_parts) if subtitle_parts else None,
                source_document_id=str(row.document_id) if row.document_id else None,
                confidence_score=row.confidence_score,
            )
        )
    return events


async def _fetch_lab_results(
    db: AsyncSession,
    member_id: uuid.UUID,
    date_from: Optional[date],
    date_to: Optional[date],
) -> List[TimelineEvent]:
    """Fetch LabResult rows (optionally filtered by test_date) and convert to TimelineEvent list."""
    stmt = select(LabResult).where(LabResult.member_id == member_id)
    if date_from is not None:
        stmt = stmt.where(LabResult.test_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(LabResult.test_date <= date_to)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    events = []
    for row in rows:
        value_str = str(row.value) if row.value is not None else row.value_text
        subtitle_parts = [p for p in [value_str, row.unit] if p]
        events.append(
            TimelineEvent(
                event_id=f"lab_result:{row.result_id}",
                event_type="LAB_RESULT",
                event_date=row.test_date,
                title=row.test_name,
                subtitle=" ".join(subtitle_parts) if subtitle_parts else None,
                source_document_id=str(row.document_id) if row.document_id else None,
                confidence_score=row.confidence_score,
            )
        )
    return events


async def _fetch_diagnoses(
    db: AsyncSession,
    member_id: uuid.UUID,
) -> List[TimelineEvent]:
    """Fetch Diagnosis rows and convert to TimelineEvent list."""
    result = await db.execute(
        select(Diagnosis).where(Diagnosis.member_id == member_id)
    )
    rows = result.scalars().all()
    events = []
    for row in rows:
        events.append(
            TimelineEvent(
                event_id=f"diagnosis:{row.diagnosis_id}",
                event_type="DIAGNOSIS",
                event_date=None,
                title=row.condition_name,
                subtitle=row.status,
                source_document_id=str(row.document_id) if row.document_id else None,
                confidence_score=row.confidence_score,
            )
        )
    return events


async def _fetch_allergies(
    db: AsyncSession,
    member_id: uuid.UUID,
) -> List[TimelineEvent]:
    """Fetch Allergy rows and convert to TimelineEvent list."""
    result = await db.execute(
        select(Allergy).where(Allergy.member_id == member_id)
    )
    rows = result.scalars().all()
    events = []
    for row in rows:
        events.append(
            TimelineEvent(
                event_id=f"allergy:{row.allergy_id}",
                event_type="ALLERGY",
                event_date=None,
                title=row.allergen_name,
                subtitle=row.reaction_type,
                source_document_id=str(row.document_id) if row.document_id else None,
                confidence_score=row.confidence_score,
            )
        )
    return events


async def _fetch_vitals(
    db: AsyncSession,
    member_id: uuid.UUID,
) -> List[TimelineEvent]:
    """Fetch Vital rows and convert to TimelineEvent list."""
    result = await db.execute(
        select(Vital).where(Vital.member_id == member_id)
    )
    rows = result.scalars().all()
    events = []
    for row in rows:
        value_str = str(row.value) if row.value is not None else None
        subtitle_parts = [p for p in [value_str, row.unit] if p]
        events.append(
            TimelineEvent(
                event_id=f"vital:{row.vital_id}",
                event_type="VITAL",
                event_date=None,
                title=row.vital_type,
                subtitle=" ".join(subtitle_parts) if subtitle_parts else None,
                source_document_id=str(row.document_id) if row.document_id else None,
                confidence_score=row.confidence_score,
            )
        )
    return events


async def _fetch_documents(
    db: AsyncSession,
    member_id: uuid.UUID,
    date_from: Optional[date],
    date_to: Optional[date],
) -> List[TimelineEvent]:
    """Fetch Document rows (optionally filtered by document_date) and convert to TimelineEvent list."""
    stmt = select(Document).where(Document.member_id == member_id)
    if date_from is not None:
        stmt = stmt.where(Document.document_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Document.document_date <= date_to)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    events = []
    for row in rows:
        title = row.original_filename or row.document_type
        events.append(
            TimelineEvent(
                event_id=f"document:{row.document_id}",
                event_type="DOCUMENT",
                event_date=row.document_date,
                title=title,
                subtitle=row.processing_status,
                source_document_id=str(row.document_id),
                confidence_score=None,
            )
        )
    return events


async def _fetch_encounters(
    db: AsyncSession,
    member_id: uuid.UUID,
    date_from: Optional[date],
    date_to: Optional[date],
) -> List[TimelineEvent]:
    """Fetch MedicalEncounter rows (provider-logged visits) and convert to TimelineEvent list."""
    stmt = select(MedicalEncounter).where(MedicalEncounter.patient_member_id == member_id)
    if date_from is not None:
        stmt = stmt.where(MedicalEncounter.encounter_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(MedicalEncounter.encounter_date <= date_to)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    events = []
    for row in rows:
        subtitle = row.diagnosis_notes[:80] if row.diagnosis_notes else None
        events.append(
            TimelineEvent(
                event_id=f"encounter:{row.encounter_id}",
                event_type="VISIT",
                event_date=row.encounter_date,
                title=row.chief_complaint or "Medical Encounter",
                subtitle=subtitle,
                source_document_id=None,
                confidence_score=None,
            )
        )
    return events


def _sort_events_desc(events: List[TimelineEvent]) -> List[TimelineEvent]:
    """Sort events by event_date descending; events with None date go last."""
    with_date = [e for e in events if e.event_date is not None]
    without_date = [e for e in events if e.event_date is None]
    with_date.sort(key=lambda e: e.event_date, reverse=True)  # type: ignore[arg-type]
    return with_date + without_date


# ---------------------------------------------------------------------------
# GET /timeline/
# ---------------------------------------------------------------------------


@router.get("/", response_model=TimelineResponse)
async def get_timeline(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    event_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> TimelineResponse:
    """Return a paginated, filterable timeline of all health events for a family member."""
    # Validate pagination
    if page < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="page_size must be between 1 and 100")

    # Validate event_type filter
    if event_type is not None and event_type not in _VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid event_type. Must be one of: {', '.join(sorted(_VALID_EVENT_TYPES))}",
        )

    # Parse date filters
    parsed_date_from = _parse_date(date_from, "date_from")
    parsed_date_to = _parse_date(date_to, "date_to")

    # Verify member ownership
    member = await _load_member_or_404(db, member_id, current_user)

    # Fetch events from each entity table
    all_events: List[TimelineEvent] = []

    if event_type is None or event_type == "MEDICATION":
        all_events.extend(await _fetch_medications(db, member.member_id))

    if event_type is None or event_type == "LAB_RESULT":
        all_events.extend(
            await _fetch_lab_results(db, member.member_id, parsed_date_from, parsed_date_to)
        )

    if event_type is None or event_type == "DIAGNOSIS":
        all_events.extend(await _fetch_diagnoses(db, member.member_id))

    if event_type is None or event_type == "ALLERGY":
        all_events.extend(await _fetch_allergies(db, member.member_id))

    if event_type is None or event_type == "VITAL":
        all_events.extend(await _fetch_vitals(db, member.member_id))

    if event_type is None or event_type == "DOCUMENT":
        all_events.extend(
            await _fetch_documents(db, member.member_id, parsed_date_from, parsed_date_to)
        )

    if event_type is None or event_type == "VISIT":
        all_events.extend(
            await _fetch_encounters(db, member.member_id, parsed_date_from, parsed_date_to)
        )

    # Sort merged list (newest first, None dates last)
    sorted_events = _sort_events_desc(all_events)

    # Total after filtering (event_type filter already applied above via selective fetching)
    total = len(sorted_events)

    # Apply pagination
    offset = (page - 1) * page_size
    page_items = sorted_events[offset: offset + page_size]

    logger.info(
        "Timeline retrieved",
        extra={
            "member_id": str(member.member_id),
            "total_events": total,
            "page": page,
            "page_size": page_size,
        },
    )

    return TimelineResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        member_id=str(member.member_id),
    )
