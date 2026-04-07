"""Profile API — GET health profile and summary for a family member."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.family_member import FamilyMember
from app.schemas.profile import HealthProfileResponse, MedicationSchema, LabResultSchema, DiagnosisSchema, ProfileSummaryResponse
from app.services import profile_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_member_or_404(
    db: DbSession,
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


# ---------------------------------------------------------------------------
# GET /profile/
# ---------------------------------------------------------------------------


@router.get("/", response_model=HealthProfileResponse)
async def get_profile(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> HealthProfileResponse:
    """Return the full health profile for a family member (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)

    profile_rm = await profile_service.get_health_profile(db, member.member_id)

    medications = [
        MedicationSchema(
            medication_id=med.medication_id,
            member_id=str(member.member_id),
            document_id=med.source_document_id,
            drug_name=med.drug_name,
            dosage=med.dosage,
            frequency=med.frequency,
            duration=None,
            route=med.route,
            confidence_score=med.confidence,
            is_active=med.is_active,
        )
        for med in profile_rm.medications
    ]

    lab_results = [
        LabResultSchema(
            lab_result_id=lab.lab_result_id,
            member_id=str(member.member_id),
            document_id=lab.source_document_id,
            test_name=lab.test_name,
            value=lab.value,
            unit=lab.unit,
            reference_range=None,
            is_abnormal=None,
            confidence_score=lab.confidence,
            test_date=lab.recorded_at.date() if lab.recorded_at is not None else None,
        )
        for lab in profile_rm.lab_results
    ]

    diagnoses = [
        DiagnosisSchema(
            diagnosis_id=diag.diagnosis_id,
            member_id=str(member.member_id),
            document_id=diag.source_document_id,
            condition_name=diag.condition_name,
            confidence_score=diag.confidence,
            status=diag.status,
        )
        for diag in profile_rm.diagnoses
    ]

    logger.info(
        "Health profile retrieved",
        extra={"member_id": str(member.member_id), "user_id": str(current_user.user_id)},
    )

    return HealthProfileResponse(
        member_id=str(member.member_id),
        medications=medications,
        lab_results=lab_results,
        diagnoses=diagnoses,
    )


# ---------------------------------------------------------------------------
# GET /profile/summary
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=ProfileSummaryResponse)
async def get_profile_summary(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProfileSummaryResponse:
    """Return summary counts for a family member's health profile (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)

    summary = await profile_service.get_profile_summary(db, member.member_id)

    logger.info(
        "Health profile summary retrieved",
        extra={"member_id": str(member.member_id), "user_id": str(current_user.user_id)},
    )

    return ProfileSummaryResponse(
        member_id=str(member.member_id),
        total_medications=summary["medication_count"],
        total_lab_results=summary["lab_result_count"],
        total_diagnoses=summary["diagnosis_count"],
        low_confidence_count=summary["low_confidence_count"],
    )
