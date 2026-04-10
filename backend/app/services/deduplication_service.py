"""Deduplication service — merges duplicate medical entities across documents.

After NLP extraction, the same medication/condition/allergen may appear in
multiple documents for the same member.  This service identifies those
duplicates (by normalised name), merges any non-null fields from older records
into the most-recent canonical record, and deletes the older duplicates.

Rules:
- lab_results and vitals are NEVER deduplicated (same test can legitimately
  recur with different dates/values — that's trend data).
- Entries where is_manual_entry = True are NEVER deduplicated — the user
  explicitly added them.
- PHI rule: only member_id and counts are logged.  Drug/condition/allergen
  names must never appear in log output.
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Medications
# ---------------------------------------------------------------------------

async def deduplicate_medications(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> int:
    """Merge duplicate medications for *member_id*.

    Groups by drug_name.lower().strip().  For each group with >1 non-manual
    entry, keeps the most-recently-created record as canonical, back-fills any
    None fields from older records, then deletes those older records.

    Returns the total number of records deleted.
    """
    from app.models.medication import Medication  # noqa: PLC0415

    result = await session.execute(
        select(Medication)
        .where(
            Medication.member_id == member_id,
            Medication.is_manual_entry.is_(False),
        )
        .order_by(Medication.created_at.asc())
    )
    medications: List[Medication] = list(result.scalars().all())

    groups: Dict[str, List[Medication]] = defaultdict(list)
    for med in medications:
        key = med.drug_name.lower().strip()
        groups[key].append(med)

    deleted = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue

        # Most-recently created is canonical (list is asc so last element)
        canonical = group[-1]
        older = group[:-1]

        # Back-fill None fields on canonical from older records
        _MEDICATION_MERGE_FIELDS = ("dosage", "frequency", "route", "start_date", "end_date")
        for field in _MEDICATION_MERGE_FIELDS:
            if getattr(canonical, field) is None:
                for old in reversed(older):
                    val = getattr(old, field)
                    if val is not None:
                        setattr(canonical, field, val)
                        break

        # Delete older duplicates
        for old in older:
            await session.delete(old)
            deleted += 1

    if deleted:
        await session.commit()
        logger.info(
            "Medications deduplicated",
            extra={"member_id": str(member_id), "deleted": deleted},
        )

    return deleted


# ---------------------------------------------------------------------------
# Diagnoses
# ---------------------------------------------------------------------------

async def deduplicate_diagnoses(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> int:
    """Merge duplicate diagnoses for *member_id*.

    Groups by condition_name.lower().strip().  Keeps the most-recent record,
    merges icd10_code and status from older records if they are None on the
    canonical, deletes older duplicates.

    Returns the total number of records deleted.
    """
    from app.models.diagnosis import Diagnosis  # noqa: PLC0415

    result = await session.execute(
        select(Diagnosis)
        .where(
            Diagnosis.member_id == member_id,
            Diagnosis.is_manual_entry.is_(False),
        )
        .order_by(Diagnosis.created_at.asc())
    )
    diagnoses: List[Diagnosis] = list(result.scalars().all())

    groups: Dict[str, List[Diagnosis]] = defaultdict(list)
    for diag in diagnoses:
        key = diag.condition_name.lower().strip()
        groups[key].append(diag)

    deleted = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue

        canonical = group[-1]
        older = group[:-1]

        _DIAGNOSIS_MERGE_FIELDS = ("icd10_code", "status")
        for field in _DIAGNOSIS_MERGE_FIELDS:
            if getattr(canonical, field) is None:
                for old in reversed(older):
                    val = getattr(old, field)
                    if val is not None:
                        setattr(canonical, field, val)
                        break

        for old in older:
            await session.delete(old)
            deleted += 1

    if deleted:
        await session.commit()
        logger.info(
            "Diagnoses deduplicated",
            extra={"member_id": str(member_id), "deleted": deleted},
        )

    return deleted


# ---------------------------------------------------------------------------
# Allergies
# ---------------------------------------------------------------------------

async def deduplicate_allergies(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> int:
    """Merge duplicate allergies for *member_id*.

    Groups by allergen_name.lower().strip().  Keeps the most-recent record,
    merges reaction_type and severity from older records if they are None on
    the canonical, deletes older duplicates.

    Returns the total number of records deleted.
    """
    from app.models.allergy import Allergy  # noqa: PLC0415

    result = await session.execute(
        select(Allergy)
        .where(
            Allergy.member_id == member_id,
            Allergy.is_manual_entry.is_(False),
        )
        .order_by(Allergy.created_at.asc())
    )
    allergies: List[Allergy] = list(result.scalars().all())

    groups: Dict[str, List[Allergy]] = defaultdict(list)
    for allergy in allergies:
        key = allergy.allergen_name.lower().strip()
        groups[key].append(allergy)

    deleted = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue

        canonical = group[-1]
        older = group[:-1]

        _ALLERGY_MERGE_FIELDS = ("reaction_type", "severity")
        for field in _ALLERGY_MERGE_FIELDS:
            if getattr(canonical, field) is None:
                for old in reversed(older):
                    val = getattr(old, field)
                    if val is not None:
                        setattr(canonical, field, val)
                        break

        for old in older:
            await session.delete(old)
            deleted += 1

    if deleted:
        await session.commit()
        logger.info(
            "Allergies deduplicated",
            extra={"member_id": str(member_id), "deleted": deleted},
        )

    return deleted


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_deduplication(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> dict:
    """Run deduplication for all entity types for *member_id*.

    Returns a dict with counts of deleted records per entity type::

        {"medications": 2, "diagnoses": 1, "allergies": 0}

    lab_results and vitals are intentionally excluded — they represent
    time-series trend data where repetition is expected.
    """
    medications_deleted = await deduplicate_medications(session, member_id)
    diagnoses_deleted = await deduplicate_diagnoses(session, member_id)
    allergies_deleted = await deduplicate_allergies(session, member_id)

    counts = {
        "medications": medications_deleted,
        "diagnoses": diagnoses_deleted,
        "allergies": allergies_deleted,
    }

    logger.info(
        "Deduplication complete",
        extra={"member_id": str(member_id), **counts},
    )
    return counts
