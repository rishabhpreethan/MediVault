"""Entity CRUD API — manual add/edit/delete for all 5 health entity types (MV-053).

All manually-created entities have is_manual_entry=True and document_id=None.
Ownership is verified via the require_member_access pattern from profile.py.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.models.vital import Vital
from app.schemas.entity_crud import (
    AllergyCreate,
    AllergyResponse,
    AllergyUpdate,
    DiagnosisCreate,
    DiagnosisResponse,
    DiagnosisUpdate,
    LabResultCreate,
    LabResultResponse,
    LabResultUpdate,
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
    VitalCreate,
    VitalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


async def _load_member_or_404(
    db: DbSession,
    member_id: uuid.UUID,
    current_user,
) -> FamilyMember:
    """Load a FamilyMember row and verify ownership, or raise 404/403."""
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
# Medications
# ---------------------------------------------------------------------------


@router.post(
    "/profile/{member_id}/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medication(
    member_id: uuid.UUID,
    body: MedicationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> MedicationResponse:
    """Manually create a medication for a family member."""
    member = await _load_member_or_404(db, member_id, current_user)

    med = Medication(
        member_id=member.member_id,
        document_id=None,
        drug_name=body.drug_name,
        dosage=body.dosage,
        frequency=body.frequency,
        route=body.route,
        start_date=body.start_date,
        end_date=body.end_date,
        is_active=body.is_active,
        confidence_score="HIGH",
        is_manual_entry=True,
    )
    db.add(med)
    await db.commit()
    await db.refresh(med)

    logger.info(
        "Manual medication created",
        extra={"medication_id": str(med.medication_id), "member_id": str(member.member_id)},
    )

    return MedicationResponse(
        medication_id=str(med.medication_id),
        member_id=str(med.member_id),
        drug_name=med.drug_name,
        drug_name_normalized=med.drug_name_normalized,
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        start_date=med.start_date,
        end_date=med.end_date,
        is_active=med.is_active,
        confidence_score=med.confidence_score,
        is_manual_entry=med.is_manual_entry,
    )


@router.put(
    "/profile/{member_id}/medications/{med_id}",
    response_model=MedicationResponse,
)
async def update_medication(
    member_id: uuid.UUID,
    med_id: uuid.UUID,
    body: MedicationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> MedicationResponse:
    """Update a medication entry (partial update — only provided fields are changed)."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Medication).where(
            Medication.medication_id == med_id,
            Medication.member_id == member.member_id,
        )
    )
    med = result.scalar_one_or_none()
    if med is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    await db.commit()
    await db.refresh(med)

    logger.info(
        "Medication updated",
        extra={"medication_id": str(med.medication_id), "member_id": str(member.member_id)},
    )

    return MedicationResponse(
        medication_id=str(med.medication_id),
        member_id=str(med.member_id),
        drug_name=med.drug_name,
        drug_name_normalized=med.drug_name_normalized,
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        start_date=med.start_date,
        end_date=med.end_date,
        is_active=med.is_active,
        confidence_score=med.confidence_score,
        is_manual_entry=med.is_manual_entry,
    )


@router.delete(
    "/profile/{member_id}/medications/{med_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_medication(
    member_id: uuid.UUID,
    med_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a medication entry."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Medication).where(
            Medication.medication_id == med_id,
            Medication.member_id == member.member_id,
        )
    )
    med = result.scalar_one_or_none()
    if med is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    await db.delete(med)
    await db.commit()

    logger.info(
        "Medication deleted",
        extra={"medication_id": str(med_id), "member_id": str(member.member_id)},
    )


@router.patch(
    "/profile/{member_id}/medications/{med_id}/discontinue",
    response_model=MedicationResponse,
)
async def discontinue_medication(
    member_id: uuid.UUID,
    med_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MedicationResponse:
    """Mark a medication as discontinued (is_active=False)."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Medication).where(
            Medication.medication_id == med_id,
            Medication.member_id == member.member_id,
        )
    )
    med = result.scalar_one_or_none()
    if med is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    med.is_active = False
    await db.commit()
    await db.refresh(med)

    logger.info(
        "Medication discontinued",
        extra={"medication_id": str(med.medication_id), "member_id": str(member.member_id)},
    )

    return MedicationResponse(
        medication_id=str(med.medication_id),
        member_id=str(med.member_id),
        drug_name=med.drug_name,
        drug_name_normalized=med.drug_name_normalized,
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        start_date=med.start_date,
        end_date=med.end_date,
        is_active=med.is_active,
        confidence_score=med.confidence_score,
        is_manual_entry=med.is_manual_entry,
    )


# ---------------------------------------------------------------------------
# Lab Results
# ---------------------------------------------------------------------------


@router.post(
    "/profile/{member_id}/lab-results",
    response_model=LabResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lab_result(
    member_id: uuid.UUID,
    body: LabResultCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> LabResultResponse:
    """Manually create a lab result for a family member."""
    member = await _load_member_or_404(db, member_id, current_user)

    lab = LabResult(
        member_id=member.member_id,
        document_id=None,
        test_name=body.test_name,
        value=body.value,
        value_text=body.value_text,
        unit=body.unit,
        reference_low=body.reference_low,
        reference_high=body.reference_high,
        flag=body.flag,
        test_date=body.test_date,
        confidence_score="HIGH",
        is_manual_entry=True,
    )
    db.add(lab)
    await db.commit()
    await db.refresh(lab)

    logger.info(
        "Manual lab result created",
        extra={"result_id": str(lab.result_id), "member_id": str(member.member_id)},
    )

    return LabResultResponse(
        result_id=str(lab.result_id),
        member_id=str(lab.member_id),
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


@router.put(
    "/profile/{member_id}/lab-results/{result_id}",
    response_model=LabResultResponse,
)
async def update_lab_result(
    member_id: uuid.UUID,
    result_id: uuid.UUID,
    body: LabResultUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> LabResultResponse:
    """Update a lab result entry (partial update)."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(LabResult).where(
            LabResult.result_id == result_id,
            LabResult.member_id == member.member_id,
        )
    )
    lab = result.scalar_one_or_none()
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab result not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)

    await db.commit()
    await db.refresh(lab)

    logger.info(
        "Lab result updated",
        extra={"result_id": str(lab.result_id), "member_id": str(member.member_id)},
    )

    return LabResultResponse(
        result_id=str(lab.result_id),
        member_id=str(lab.member_id),
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


@router.delete(
    "/profile/{member_id}/lab-results/{result_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_lab_result(
    member_id: uuid.UUID,
    result_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a lab result entry."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(LabResult).where(
            LabResult.result_id == result_id,
            LabResult.member_id == member.member_id,
        )
    )
    lab = result.scalar_one_or_none()
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab result not found")

    await db.delete(lab)
    await db.commit()

    logger.info(
        "Lab result deleted",
        extra={"result_id": str(result_id), "member_id": str(member.member_id)},
    )


# ---------------------------------------------------------------------------
# Diagnoses
# ---------------------------------------------------------------------------


@router.post(
    "/profile/{member_id}/diagnoses",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_diagnosis(
    member_id: uuid.UUID,
    body: DiagnosisCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DiagnosisResponse:
    """Manually create a diagnosis for a family member."""
    member = await _load_member_or_404(db, member_id, current_user)

    diag = Diagnosis(
        member_id=member.member_id,
        document_id=None,
        condition_name=body.condition_name,
        icd10_code=body.icd10_code,
        diagnosed_date=body.diagnosed_date,
        status=body.status,
        confidence_score="HIGH",
        is_manual_entry=True,
    )
    db.add(diag)
    await db.commit()
    await db.refresh(diag)

    logger.info(
        "Manual diagnosis created",
        extra={"diagnosis_id": str(diag.diagnosis_id), "member_id": str(member.member_id)},
    )

    return DiagnosisResponse(
        diagnosis_id=str(diag.diagnosis_id),
        member_id=str(diag.member_id),
        condition_name=diag.condition_name,
        condition_normalized=diag.condition_normalized,
        icd10_code=diag.icd10_code,
        diagnosed_date=diag.diagnosed_date,
        status=diag.status,
        confidence_score=diag.confidence_score,
        is_manual_entry=diag.is_manual_entry,
    )


@router.put(
    "/profile/{member_id}/diagnoses/{diag_id}",
    response_model=DiagnosisResponse,
)
async def update_diagnosis(
    member_id: uuid.UUID,
    diag_id: uuid.UUID,
    body: DiagnosisUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> DiagnosisResponse:
    """Update a diagnosis entry (partial update)."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Diagnosis).where(
            Diagnosis.diagnosis_id == diag_id,
            Diagnosis.member_id == member.member_id,
        )
    )
    diag = result.scalar_one_or_none()
    if diag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(diag, field, value)

    await db.commit()
    await db.refresh(diag)

    logger.info(
        "Diagnosis updated",
        extra={"diagnosis_id": str(diag.diagnosis_id), "member_id": str(member.member_id)},
    )

    return DiagnosisResponse(
        diagnosis_id=str(diag.diagnosis_id),
        member_id=str(diag.member_id),
        condition_name=diag.condition_name,
        condition_normalized=diag.condition_normalized,
        icd10_code=diag.icd10_code,
        diagnosed_date=diag.diagnosed_date,
        status=diag.status,
        confidence_score=diag.confidence_score,
        is_manual_entry=diag.is_manual_entry,
    )


@router.delete(
    "/profile/{member_id}/diagnoses/{diag_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_diagnosis(
    member_id: uuid.UUID,
    diag_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a diagnosis entry."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Diagnosis).where(
            Diagnosis.diagnosis_id == diag_id,
            Diagnosis.member_id == member.member_id,
        )
    )
    diag = result.scalar_one_or_none()
    if diag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")

    await db.delete(diag)
    await db.commit()

    logger.info(
        "Diagnosis deleted",
        extra={"diagnosis_id": str(diag_id), "member_id": str(member.member_id)},
    )


# ---------------------------------------------------------------------------
# Allergies
# ---------------------------------------------------------------------------


@router.post(
    "/profile/{member_id}/allergies",
    response_model=AllergyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_allergy(
    member_id: uuid.UUID,
    body: AllergyCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> AllergyResponse:
    """Manually create an allergy entry for a family member."""
    member = await _load_member_or_404(db, member_id, current_user)

    allergy = Allergy(
        member_id=member.member_id,
        document_id=None,
        allergen_name=body.allergen_name,
        reaction_type=body.reaction_type,
        severity=body.severity,
        confidence_score="HIGH",
        is_manual_entry=True,
    )
    db.add(allergy)
    await db.commit()
    await db.refresh(allergy)

    logger.info(
        "Manual allergy created",
        extra={"allergy_id": str(allergy.allergy_id), "member_id": str(member.member_id)},
    )

    return AllergyResponse(
        allergy_id=str(allergy.allergy_id),
        member_id=str(allergy.member_id),
        allergen_name=allergy.allergen_name,
        reaction_type=allergy.reaction_type,
        severity=allergy.severity,
        confidence_score=allergy.confidence_score,
        is_manual_entry=allergy.is_manual_entry,
    )


@router.put(
    "/profile/{member_id}/allergies/{allergy_id}",
    response_model=AllergyResponse,
)
async def update_allergy(
    member_id: uuid.UUID,
    allergy_id: uuid.UUID,
    body: AllergyUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> AllergyResponse:
    """Update an allergy entry (partial update)."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Allergy).where(
            Allergy.allergy_id == allergy_id,
            Allergy.member_id == member.member_id,
        )
    )
    allergy = result.scalar_one_or_none()
    if allergy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(allergy, field, value)

    await db.commit()
    await db.refresh(allergy)

    logger.info(
        "Allergy updated",
        extra={"allergy_id": str(allergy.allergy_id), "member_id": str(member.member_id)},
    )

    return AllergyResponse(
        allergy_id=str(allergy.allergy_id),
        member_id=str(allergy.member_id),
        allergen_name=allergy.allergen_name,
        reaction_type=allergy.reaction_type,
        severity=allergy.severity,
        confidence_score=allergy.confidence_score,
        is_manual_entry=allergy.is_manual_entry,
    )


@router.delete(
    "/profile/{member_id}/allergies/{allergy_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_allergy(
    member_id: uuid.UUID,
    allergy_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete an allergy entry."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Allergy).where(
            Allergy.allergy_id == allergy_id,
            Allergy.member_id == member.member_id,
        )
    )
    allergy = result.scalar_one_or_none()
    if allergy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")

    await db.delete(allergy)
    await db.commit()

    logger.info(
        "Allergy deleted",
        extra={"allergy_id": str(allergy_id), "member_id": str(member.member_id)},
    )


# ---------------------------------------------------------------------------
# Vitals
# ---------------------------------------------------------------------------


@router.post(
    "/profile/{member_id}/vitals",
    response_model=VitalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vital(
    member_id: uuid.UUID,
    body: VitalCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> VitalResponse:
    """Manually create a vital reading for a family member."""
    member = await _load_member_or_404(db, member_id, current_user)

    vital = Vital(
        member_id=member.member_id,
        document_id=None,
        vital_type=body.vital_type,
        value=body.value,
        unit=body.unit,
        recorded_date=body.recorded_date,
        confidence_score="HIGH",
    )
    db.add(vital)
    await db.commit()
    await db.refresh(vital)

    logger.info(
        "Manual vital created",
        extra={"vital_id": str(vital.vital_id), "member_id": str(member.member_id)},
    )

    return VitalResponse(
        vital_id=str(vital.vital_id),
        member_id=str(vital.member_id),
        vital_type=vital.vital_type,
        value=float(vital.value),
        unit=vital.unit,
        recorded_date=vital.recorded_date,
        confidence_score=vital.confidence_score,
    )


@router.delete(
    "/profile/{member_id}/vitals/{vital_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_vital(
    member_id: uuid.UUID,
    vital_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a vital reading."""
    member = await _load_member_or_404(db, member_id, current_user)

    result = await db.execute(
        select(Vital).where(
            Vital.vital_id == vital_id,
            Vital.member_id == member.member_id,
        )
    )
    vital = result.scalar_one_or_none()
    if vital is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital not found")

    await db.delete(vital)
    await db.commit()

    logger.info(
        "Vital deleted",
        extra={"vital_id": str(vital_id), "member_id": str(member.member_id)},
    )
