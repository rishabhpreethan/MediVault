"""MV-050: Profile aggregation service — builds a unified health profile read model."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.models.lab_result import LabResult
from app.models.medication import Medication


# ---------------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------------

@dataclass
class MedicationRM:
    """Read model for a single medication record."""

    medication_id: str
    drug_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    confidence: str
    is_active: bool
    source_document_id: Optional[str]


@dataclass
class LabResultRM:
    """Read model for a single lab result record."""

    lab_result_id: str
    test_name: str
    value: Optional[str]  # Decimal stored as string to preserve precision
    unit: Optional[str]
    confidence: str
    recorded_at: Optional[datetime]
    source_document_id: Optional[str]


@dataclass
class DiagnosisRM:
    """Read model for a single diagnosis record."""

    diagnosis_id: str
    condition_name: str
    status: str
    confidence: str
    source_document_id: Optional[str]


@dataclass
class HealthProfileRM:
    """Aggregated health profile read model for a family member."""

    member_id: str
    medications: list[MedicationRM] = field(default_factory=list)
    lab_results: list[LabResultRM] = field(default_factory=list)
    diagnoses: list[DiagnosisRM] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _medication_to_rm(med: Medication) -> MedicationRM:
    return MedicationRM(
        medication_id=str(med.medication_id),
        drug_name=med.drug_name,
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        confidence=med.confidence_score,
        is_active=med.is_active,
        source_document_id=str(med.document_id) if med.document_id is not None else None,
    )


def _lab_result_to_rm(lab: LabResult) -> LabResultRM:
    # Prefer value_text if available; fall back to stringifying the Decimal value
    if lab.value_text is not None:
        value_str: Optional[str] = lab.value_text
    elif lab.value is not None:
        value_str = str(lab.value)
    else:
        value_str = None

    # test_date is a date; recorded_at in the RM uses datetime for ordering
    recorded_at: Optional[datetime] = None
    if lab.test_date is not None:
        recorded_at = datetime(
            lab.test_date.year,
            lab.test_date.month,
            lab.test_date.day,
            tzinfo=timezone.utc,
        )

    return LabResultRM(
        lab_result_id=str(lab.result_id),
        test_name=lab.test_name,
        value=value_str,
        unit=lab.unit,
        confidence=lab.confidence_score,
        recorded_at=recorded_at,
        source_document_id=str(lab.document_id) if lab.document_id is not None else None,
    )


def _diagnosis_to_rm(diag: Diagnosis) -> DiagnosisRM:
    return DiagnosisRM(
        diagnosis_id=str(diag.diagnosis_id),
        condition_name=diag.condition_name,
        status=diag.status,
        confidence=diag.confidence_score,
        source_document_id=str(diag.document_id) if diag.document_id is not None else None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_health_profile(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> HealthProfileRM:
    """Build a unified HealthProfileRM for the given family member.

    Queries the Medication, LabResult, and Diagnosis tables filtered by
    ``member_id``.  Only active medications are included (``is_active=True``).
    Lab results are ordered by ``test_date`` descending (most recent first).

    PHI rule: member_id is safe to log as an identifier; no clinical values
    are written to any log output.

    Args:
        session: An active async SQLAlchemy session.
        member_id: UUID of the target FamilyMember.

    Returns:
        HealthProfileRM populated with all three entity lists.
    """
    # --- Medications (active only) ---
    med_stmt = (
        select(Medication)
        .where(Medication.member_id == member_id)
        .where(Medication.is_active.is_(True))
    )
    med_result = await session.execute(med_stmt)
    medications = [_medication_to_rm(m) for m in med_result.scalars().all()]

    # --- Lab results (ordered by test_date desc) ---
    lab_stmt = (
        select(LabResult)
        .where(LabResult.member_id == member_id)
        .order_by(LabResult.test_date.desc().nulls_last())
    )
    lab_result = await session.execute(lab_stmt)
    lab_results = [_lab_result_to_rm(lr) for lr in lab_result.scalars().all()]

    # --- Diagnoses ---
    diag_stmt = select(Diagnosis).where(Diagnosis.member_id == member_id)
    diag_result = await session.execute(diag_stmt)
    diagnoses = [_diagnosis_to_rm(d) for d in diag_result.scalars().all()]

    return HealthProfileRM(
        member_id=str(member_id),
        medications=medications,
        lab_results=lab_results,
        diagnoses=diagnoses,
        generated_at=datetime.now(tz=timezone.utc),
    )


async def get_profile_summary(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> dict:
    """Return counts for the health profile of a family member.

    Counts include all entities (medications, lab results, diagnoses) and
    a cross-entity ``low_confidence_count`` for items flagged as LOW.

    Args:
        session: An active async SQLAlchemy session.
        member_id: UUID of the target FamilyMember.

    Returns:
        dict with keys:
        - ``medication_count`` (int)
        - ``lab_result_count`` (int)
        - ``diagnosis_count`` (int)
        - ``low_confidence_count`` (int)
    """
    profile = await get_health_profile(session, member_id)

    low_confidence_count = sum(
        1
        for item in (
            *profile.medications,
            *profile.lab_results,
            *profile.diagnoses,
        )
        if item.confidence == "LOW"
    )

    return {
        "medication_count": len(profile.medications),
        "lab_result_count": len(profile.lab_results),
        "diagnosis_count": len(profile.diagnoses),
        "low_confidence_count": low_confidence_count,
    }
