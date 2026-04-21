"""Provider / Doctor Workflow API — MV-156, MV-157.

Endpoints:
  POST /provider/patient-lookup          — validate passport, create access request
  GET  /provider/access-requests/:id/status — polling for provider waiting screen
  POST /provider/access-requests/:id/respond — patient accepts/declines
  GET  /provider/patient/:requestId      — full patient data (ACCEPTED only)
  POST /provider/encounters              — log an encounter
  GET  /provider/patient/:requestId/encounters — list encounters for a request
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis
from app.models.family_member import FamilyMember
from app.models.medical_encounter import MedicalEncounter
from app.models.medication import Medication
from app.models.notification import Notification
from app.models.passport import SharedPassport
from app.models.provider_access_request import ProviderAccessRequest
from app.models.user import User
from app.schemas.provider import (
    AccessRequestStatusResponse,
    EncounterResponse,
    LogEncounterRequest,
    PatientDataResponse,
    PatientLookupRequest,
    PatientLookupResponse,
    PatientSummary,
    RespondToRequestBody,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_ACCESS_REQUEST_TTL_MINUTES = 15


def _require_provider(current_user: User) -> None:
    if current_user.role != "PROVIDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider role required",
        )


# ---------------------------------------------------------------------------
# POST /provider/patient-lookup
# ---------------------------------------------------------------------------


@router.post("/patient-lookup", response_model=PatientLookupResponse)
async def patient_lookup(
    body: PatientLookupRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> PatientLookupResponse:
    """Validate a passport UUID, create a PENDING access request, notify patient."""
    _require_provider(current_user)

    # Validate passport exists and is active
    passport_result = await db.execute(
        select(SharedPassport).where(
            SharedPassport.passport_id == body.passport_id,
            SharedPassport.is_active == True,  # noqa: E712
        )
    )
    passport = passport_result.scalar_one_or_none()
    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport not found or has been revoked",
        )

    if passport.expires_at and passport.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Passport has expired",
        )

    # Get the patient's self FamilyMember
    member_result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == passport.member_id)
    )
    patient_member = member_result.scalar_one_or_none()
    if patient_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient member not found",
        )

    # Check for an existing PENDING request from this provider for this patient
    existing_result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.provider_user_id == current_user.user_id,
            ProviderAccessRequest.patient_member_id == patient_member.member_id,
            ProviderAccessRequest.status == "PENDING",
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return PatientLookupResponse(
            request_id=existing.request_id,
            status="PENDING",
            message="Access request already pending",
        )

    # Create PENDING access request
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=_ACCESS_REQUEST_TTL_MINUTES)
    access_request = ProviderAccessRequest(
        request_id=uuid.uuid4(),
        provider_user_id=current_user.user_id,
        patient_member_id=patient_member.member_id,
        passport_id_used=passport.passport_id,
        status="PENDING",
        expires_at=expires_at,
    )
    db.add(access_request)
    await db.flush()

    # Dispatch in-app notification to the patient (owner of the member)
    notification = Notification(
        notification_id=uuid.uuid4(),
        user_id=patient_member.user_id,
        type="PROVIDER_ACCESS_REQUEST",
        title="Doctor requesting access",
        body=f"A provider is requesting access to your health records. You have {_ACCESS_REQUEST_TTL_MINUTES} minutes to respond.",
        action_url=f"/notifications",
        extra_data={
            "request_id": str(access_request.request_id),
            "provider_user_id": str(current_user.user_id),
            "provider_email": current_user.email,
        },
    )
    db.add(notification)
    await db.flush()

    # Link notification back to request
    access_request.notification_id = notification.notification_id
    await db.commit()

    logger.info(
        "Access request created request_id=%s provider=%s patient_member=%s",
        access_request.request_id,
        current_user.user_id,
        patient_member.member_id,
    )

    return PatientLookupResponse(
        request_id=access_request.request_id,
        status="PENDING",
        patient_name=None,
        message="Access request sent to patient",
    )


# ---------------------------------------------------------------------------
# GET /provider/access-requests/{request_id}/status
# ---------------------------------------------------------------------------


@router.get("/access-requests/{request_id}/status", response_model=AccessRequestStatusResponse)
async def get_access_request_status(
    request_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AccessRequestStatusResponse:
    """Polling endpoint — provider checks if patient has responded."""
    _require_provider(current_user)

    result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.request_id == request_id,
            ProviderAccessRequest.provider_user_id == current_user.user_id,
        )
    )
    access_request = result.scalar_one_or_none()
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Auto-expire if past TTL
    if (
        access_request.status == "PENDING"
        and access_request.expires_at < datetime.now(tz=timezone.utc)
    ):
        access_request.status = "EXPIRED"
        await db.commit()

    return AccessRequestStatusResponse(
        request_id=access_request.request_id,
        status=access_request.status,
        responded_at=access_request.responded_at,
    )


# ---------------------------------------------------------------------------
# POST /provider/access-requests/{request_id}/respond
# ---------------------------------------------------------------------------


@router.post("/access-requests/{request_id}/respond", status_code=200)
async def respond_to_access_request(
    request_id: uuid.UUID,
    body: RespondToRequestBody,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Patient accepts or declines a provider access request."""
    if body.action not in ("accept", "decline"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="action must be 'accept' or 'decline'",
        )

    result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.request_id == request_id,
        )
    )
    access_request = result.scalar_one_or_none()
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Confirm the current user owns the patient member
    member_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.member_id == access_request.patient_member_id,
            FamilyMember.user_id == current_user.user_id,
        )
    )
    if member_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if access_request.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request is already {access_request.status}",
        )

    if access_request.expires_at < datetime.now(tz=timezone.utc):
        access_request.status = "EXPIRED"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Request has expired")

    access_request.status = "ACCEPTED" if body.action == "accept" else "DECLINED"
    access_request.responded_at = datetime.now(tz=timezone.utc)
    await db.commit()

    logger.info(
        "Access request request_id=%s responded action=%s by user_id=%s",
        request_id,
        body.action,
        current_user.user_id,
    )

    return {"status": access_request.status, "request_id": str(request_id)}


# ---------------------------------------------------------------------------
# GET /provider/patient/{request_id}  — full patient data
# ---------------------------------------------------------------------------


@router.get("/patient/{request_id}", response_model=PatientDataResponse)
async def get_patient_data(
    request_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> PatientDataResponse:
    """Return patient profile + encounters for an ACCEPTED access request."""
    _require_provider(current_user)

    result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.request_id == request_id,
            ProviderAccessRequest.provider_user_id == current_user.user_id,
        )
    )
    access_request = result.scalar_one_or_none()
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if access_request.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient has not accepted this request",
        )

    member_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.member_id == access_request.patient_member_id
        )
    )
    member = member_result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    encounters_result = await db.execute(
        select(MedicalEncounter).where(
            MedicalEncounter.access_request_id == request_id,
            MedicalEncounter.provider_user_id == current_user.user_id,
        ).order_by(MedicalEncounter.encounter_date.desc())
    )
    encounters = encounters_result.scalars().all()

    return PatientDataResponse(
        request_id=request_id,
        patient=PatientSummary(
            member_id=member.member_id,
            full_name=member.full_name,
            date_of_birth=member.date_of_birth,
            blood_group=member.blood_group,
            height_cm=getattr(member, "height_cm", None),
            weight_kg=getattr(member, "weight_kg", None),
        ),
        encounters=[
            EncounterResponse(
                encounter_id=e.encounter_id,
                provider_user_id=e.provider_user_id,
                patient_member_id=e.patient_member_id,
                access_request_id=e.access_request_id,
                encounter_date=e.encounter_date,
                chief_complaint=e.chief_complaint,
                diagnosis_notes=e.diagnosis_notes,
                prescriptions_note=e.prescriptions_note,
                follow_up_date=e.follow_up_date,
                created_at=e.created_at,
            )
            for e in encounters
        ],
    )


# ---------------------------------------------------------------------------
# POST /provider/encounters  — log encounter
# ---------------------------------------------------------------------------


@router.post("/encounters", response_model=EncounterResponse, status_code=201)
async def log_encounter(
    body: LogEncounterRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> EncounterResponse:
    """Log a medical encounter against an ACCEPTED access request."""
    _require_provider(current_user)

    result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.request_id == body.request_id,
            ProviderAccessRequest.provider_user_id == current_user.user_id,
        )
    )
    access_request = result.scalar_one_or_none()
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if access_request.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only log encounters for ACCEPTED requests",
        )

    encounter = MedicalEncounter(
        encounter_id=uuid.uuid4(),
        provider_user_id=current_user.user_id,
        patient_member_id=access_request.patient_member_id,
        access_request_id=access_request.request_id,
        encounter_date=body.encounter_date,
        chief_complaint=body.chief_complaint,
        diagnosis_notes=body.diagnosis_notes,
        prescriptions_note=body.prescriptions_note,
        follow_up_date=body.follow_up_date,
    )
    db.add(encounter)

    for d in body.diagnoses:
        db.add(Diagnosis(
            diagnosis_id=uuid.uuid4(),
            member_id=access_request.patient_member_id,
            condition_name=d.condition_name,
            status=d.status,
            diagnosed_date=body.encounter_date,
            is_manual_entry=True,
            confidence_score="HIGH",
        ))

    for m in body.medications:
        db.add(Medication(
            medication_id=uuid.uuid4(),
            member_id=access_request.patient_member_id,
            drug_name=m.drug_name,
            dosage=m.dosage,
            frequency=m.frequency,
            is_active=m.is_active,
            start_date=body.encounter_date,
            is_manual_entry=True,
            confidence_score="HIGH",
        ))

    await db.commit()
    await db.refresh(encounter)

    logger.info(
        "Encounter logged encounter_id=%s provider=%s patient_member=%s",
        encounter.encounter_id,
        current_user.user_id,
        access_request.patient_member_id,
    )

    return EncounterResponse(
        encounter_id=encounter.encounter_id,
        provider_user_id=encounter.provider_user_id,
        patient_member_id=encounter.patient_member_id,
        access_request_id=encounter.access_request_id,
        encounter_date=encounter.encounter_date,
        chief_complaint=encounter.chief_complaint,
        diagnosis_notes=encounter.diagnosis_notes,
        prescriptions_note=encounter.prescriptions_note,
        follow_up_date=encounter.follow_up_date,
        created_at=encounter.created_at,
    )


# ---------------------------------------------------------------------------
# GET /provider/patient/{request_id}/encounters
# ---------------------------------------------------------------------------


@router.get("/patient/{request_id}/encounters", response_model=list[EncounterResponse])
async def list_encounters(
    request_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[EncounterResponse]:
    """List all encounters logged under an access request."""
    _require_provider(current_user)

    result = await db.execute(
        select(ProviderAccessRequest).where(
            ProviderAccessRequest.request_id == request_id,
            ProviderAccessRequest.provider_user_id == current_user.user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    enc_result = await db.execute(
        select(MedicalEncounter).where(
            MedicalEncounter.access_request_id == request_id,
            MedicalEncounter.provider_user_id == current_user.user_id,
        ).order_by(MedicalEncounter.encounter_date.desc())
    )
    encounters = enc_result.scalars().all()

    return [
        EncounterResponse(
            encounter_id=e.encounter_id,
            provider_user_id=e.provider_user_id,
            patient_member_id=e.patient_member_id,
            access_request_id=e.access_request_id,
            encounter_date=e.encounter_date,
            chief_complaint=e.chief_complaint,
            diagnosis_notes=e.diagnosis_notes,
            prescriptions_note=e.prescriptions_note,
            follow_up_date=e.follow_up_date,
            created_at=e.created_at,
        )
        for e in encounters
    ]
