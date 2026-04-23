"""Profile API — GET health profile and summary for a family member."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_vault_access
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.models.vital import Vital
from app.models.medical_encounter import MedicalEncounter
from app.models.user import User
from app.schemas.profile import (
    AllergySchema,
    DiagnosisSchema,
    EncounterListResponse,
    EncounterResponse,
    FamilyMemberSchema,
    HealthProfileResponse,
    LabResultSchema,
    MedicationSchema,
    ProfileSummaryResponse,
    VitalSchema,
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


@router.get("/", response_model=HealthProfileResponse)
async def get_profile(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> HealthProfileResponse:
    """Return the full health profile for a family member (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)

    # Medications (active first, then inactive)
    med_rows = (await db.execute(
        select(Medication)
        .where(Medication.member_id == member.member_id)
        .order_by(Medication.is_active.desc(), Medication.created_at.desc())
    )).scalars().all()

    # Lab results (most recent first, deduplicated by test_name keeping latest)
    lab_rows = (await db.execute(
        select(LabResult)
        .where(LabResult.member_id == member.member_id)
        .order_by(LabResult.test_date.desc().nulls_last(), LabResult.created_at.desc())
    )).scalars().all()

    # Deduplicate lab results: keep the most recent entry per test name
    seen_tests: set[str] = set()
    recent_labs: list[LabResult] = []
    for lab in lab_rows:
        key = (lab.test_name_normalized or lab.test_name).lower()
        if key not in seen_tests:
            seen_tests.add(key)
            recent_labs.append(lab)

    # Diagnoses
    diag_rows = (await db.execute(
        select(Diagnosis)
        .where(Diagnosis.member_id == member.member_id)
        .order_by(Diagnosis.diagnosed_date.desc().nulls_last())
    )).scalars().all()

    # Allergies
    allergy_rows = (await db.execute(
        select(Allergy).where(Allergy.member_id == member.member_id)
    )).scalars().all()

    # Vitals (most recent reading per vital_type)
    vital_rows = (await db.execute(
        select(Vital)
        .where(Vital.member_id == member.member_id)
        .order_by(Vital.recorded_date.desc().nulls_last())
    )).scalars().all()

    seen_vital_types: set[str] = set()
    recent_vitals: list[Vital] = []
    for v in vital_rows:
        if v.vital_type not in seen_vital_types:
            seen_vital_types.add(v.vital_type)
            recent_vitals.append(v)

    logger.info(
        "Health profile retrieved",
        extra={"member_id": str(member.member_id), "user_id": str(current_user.user_id)},
    )

    return HealthProfileResponse(
        member=FamilyMemberSchema(
            member_id=str(member.member_id),
            user_id=str(member.user_id),
            full_name=member.full_name,
            relationship=member.relationship,
            date_of_birth=member.date_of_birth,
            blood_group=member.blood_group,
            is_self=member.is_self,
        ),
        medications=[
            MedicationSchema(
                medication_id=str(m.medication_id),
                drug_name=m.drug_name,
                drug_name_normalized=m.drug_name_normalized,
                dosage=m.dosage,
                frequency=m.frequency,
                route=m.route,
                start_date=m.start_date,
                end_date=m.end_date,
                is_active=m.is_active,
                confidence_score=m.confidence_score,
                is_manual_entry=m.is_manual_entry,
            )
            for m in med_rows
        ],
        diagnoses=[
            DiagnosisSchema(
                diagnosis_id=str(d.diagnosis_id),
                condition_name=d.condition_name,
                condition_normalized=d.condition_normalized,
                icd10_code=d.icd10_code,
                diagnosed_date=d.diagnosed_date,
                status=d.status,
                confidence_score=d.confidence_score,
                is_manual_entry=d.is_manual_entry,
            )
            for d in diag_rows
        ],
        allergies=[
            AllergySchema(
                allergy_id=str(a.allergy_id),
                allergen_name=a.allergen_name,
                reaction_type=a.reaction_type,
                severity=a.severity,
                confidence_score=a.confidence_score,
                is_manual_entry=a.is_manual_entry,
            )
            for a in allergy_rows
        ],
        recent_labs=[
            LabResultSchema(
                result_id=str(lab.result_id),
                test_name=lab.test_name,
                test_name_normalized=lab.test_name_normalized,
                value=float(lab.value) if lab.value is not None else None,
                value_text=lab.value_text,
                unit=lab.unit,
                reference_low=float(lab.reference_low) if lab.reference_low is not None else None,
                reference_high=float(lab.reference_high) if lab.reference_high is not None else None,
                flag=lab.flag,
                test_date=lab.test_date,
                confidence_score=lab.confidence_score,
                is_manual_entry=lab.is_manual_entry,
            )
            for lab in recent_labs
        ],
        recent_vitals=[
            VitalSchema(
                vital_id=str(v.vital_id),
                vital_type=v.vital_type,
                value=float(v.value),
                unit=v.unit,
                recorded_date=v.recorded_date,
                confidence_score=v.confidence_score,
            )
            for v in recent_vitals
        ],
    )


@router.get("/{member_id}/encounters", response_model=EncounterListResponse)
async def get_patient_encounters(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> EncounterListResponse:
    """Return all provider-logged encounters for a patient member (ownership/grant verified)."""
    await _load_member_or_404(db, member_id, current_user)

    rows = (await db.execute(
        select(MedicalEncounter)
        .where(MedicalEncounter.patient_member_id == member_id)
        .order_by(MedicalEncounter.encounter_date.desc())
    )).scalars().all()

    # Resolve provider display names via their self FamilyMember
    provider_ids = {e.provider_user_id for e in rows}
    provider_name_map: dict[uuid.UUID, str] = {}
    if provider_ids:
        self_members = (await db.execute(
            select(FamilyMember)
            .where(
                FamilyMember.user_id.in_(provider_ids),
                FamilyMember.is_self.is_(True),
            )
        )).scalars().all()
        for fm in self_members:
            if fm.user_id:
                provider_name_map[fm.user_id] = fm.full_name or "Provider"

        # Fall back to email prefix for providers without a self member
        missing = provider_ids - set(provider_name_map.keys())
        if missing:
            users = (await db.execute(
                select(User).where(User.user_id.in_(missing))
            )).scalars().all()
            for u in users:
                provider_name_map[u.user_id] = (u.email or "").split("@")[0] or "Provider"

    logger.info(
        "Patient encounters retrieved",
        extra={"member_id": str(member_id), "user_id": str(current_user.user_id)},
    )

    items = [
        EncounterResponse(
            encounter_id=str(e.encounter_id),
            encounter_date=e.encounter_date,
            provider_name=provider_name_map.get(e.provider_user_id, "Provider"),
            chief_complaint=e.chief_complaint,
            diagnosis_notes=e.diagnosis_notes,
            prescriptions_note=e.prescriptions_note,
            follow_up_date=e.follow_up_date,
        )
        for e in rows
    ]
    return EncounterListResponse(items=items, total=len(items))


@router.get("/summary", response_model=ProfileSummaryResponse)
async def get_profile_summary(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProfileSummaryResponse:
    """Return summary counts for a family member's health profile."""
    member = await _load_member_or_404(db, member_id, current_user)

    from app.services import profile_service
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
