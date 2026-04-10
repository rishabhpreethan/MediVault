"""Passport API — create, list, revoke, and publicly view Health Passports."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.family_member import FamilyMember
from app.models.medication import Medication
from app.models.passport import SharedPassport
from app.schemas.passport import (
    PassportCreate,
    PassportListResponse,
    PassportResponse,
    PublicPassportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECTION_MEDICATIONS = "medications"
_SECTION_LABS = "labs"
_SECTION_DIAGNOSES = "diagnoses"
_SECTION_ALLERGIES = "allergies"


def _sections_to_flags(visible_sections: list) -> dict:
    """Convert visible_sections JSONB list to show_* boolean flags."""
    return {
        "show_medications": _SECTION_MEDICATIONS in visible_sections,
        "show_labs": _SECTION_LABS in visible_sections,
        "show_diagnoses": _SECTION_DIAGNOSES in visible_sections,
        "show_allergies": _SECTION_ALLERGIES in visible_sections,
    }


def _flags_to_sections(
    show_medications: bool,
    show_labs: bool,
    show_diagnoses: bool,
    show_allergies: bool,
) -> list:
    """Build visible_sections JSONB list from boolean flags."""
    sections = []
    if show_medications:
        sections.append(_SECTION_MEDICATIONS)
    if show_labs:
        sections.append(_SECTION_LABS)
    if show_diagnoses:
        sections.append(_SECTION_DIAGNOSES)
    if show_allergies:
        sections.append(_SECTION_ALLERGIES)
    return sections


def _passport_to_response(passport: SharedPassport) -> PassportResponse:
    """Map ORM SharedPassport to PassportResponse schema."""
    flags = _sections_to_flags(passport.visible_sections or [])
    return PassportResponse(
        passport_id=str(passport.passport_id),
        member_id=str(passport.member_id),
        share_token=str(passport.passport_id),  # passport_id doubles as share token
        expires_at=passport.expires_at,
        is_active=passport.is_active,
        show_medications=flags["show_medications"],
        show_labs=flags["show_labs"],
        show_diagnoses=flags["show_diagnoses"],
        show_allergies=flags["show_allergies"],
        created_at=passport.created_at,
        access_count=passport.access_count,
    )


async def _load_member_or_404(
    db: DbSession,
    member_id: uuid.UUID,
    current_user,
) -> FamilyMember:
    """Load FamilyMember by ID or raise 404; verify ownership or raise 403."""
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
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/", response_model=PassportResponse, status_code=status.HTTP_201_CREATED)
async def create_passport(
    body: PassportCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> PassportResponse:
    """Create a new Health Passport for a family member."""
    try:
        member_uuid = uuid.UUID(body.member_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )

    await _load_member_or_404(db, member_uuid, current_user)

    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=body.expires_in_days)
    visible_sections = _flags_to_sections(
        body.show_medications,
        body.show_labs,
        body.show_diagnoses,
        body.show_allergies,
    )

    passport = SharedPassport(
        member_id=member_uuid,
        user_id=current_user.user_id,
        is_active=True,
        expires_at=expires_at,
        visible_sections=visible_sections,
        access_count=0,
    )
    db.add(passport)
    await db.commit()
    await db.refresh(passport)

    logger.info(
        "Passport created",
        extra={"passport_id": str(passport.passport_id), "member_id": str(passport.member_id)},
    )

    return _passport_to_response(passport)


@router.get("/", response_model=PassportListResponse)
async def list_passports(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> PassportListResponse:
    """List all passports for a family member, ordered by created_at DESC."""
    await _load_member_or_404(db, member_id, current_user)

    rows = (
        await db.execute(
            select(SharedPassport)
            .where(SharedPassport.member_id == member_id)
            .order_by(SharedPassport.created_at.desc())
        )
    ).scalars().all()

    items = [_passport_to_response(p) for p in rows]

    logger.info(
        "Passports listed",
        extra={"member_id": str(member_id), "count": len(items)},
    )

    return PassportListResponse(items=items, total=len(items))


@router.delete("/{passport_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def revoke_passport(
    passport_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Revoke (soft-delete) a Health Passport."""
    result = await db.execute(
        select(SharedPassport).where(SharedPassport.passport_id == passport_id)
    )
    passport = result.scalar_one_or_none()
    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport not found",
        )

    # Verify ownership via passport.member's user_id
    member_result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == passport.member_id)
    )
    member = member_result.scalar_one_or_none()
    if member is None or member.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    passport.is_active = False
    await db.commit()

    logger.info(
        "Passport revoked",
        extra={"passport_id": str(passport_id)},
    )


@router.get("/public/{share_token}", response_model=PublicPassportResponse)
async def view_public_passport(
    share_token: uuid.UUID,
    db: DbSession,
) -> PublicPassportResponse:
    """Public endpoint — no auth required. Load and return passport data.

    PHI logging rule: only share_token and access_count are logged — no names or values.
    """
    result = await db.execute(
        select(SharedPassport).where(SharedPassport.passport_id == share_token)
    )
    passport = result.scalar_one_or_none()

    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport not found",
        )

    # Check active and expiry — return 410 GONE if revoked or expired
    now = datetime.now(tz=timezone.utc)
    if not passport.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Passport has been revoked",
        )
    if passport.expires_at is not None and passport.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Passport has expired",
        )

    # Increment access count
    passport.access_count += 1
    await db.commit()

    logger.info(
        "Passport accessed",
        extra={
            "share_token": str(share_token),
            "access_count": passport.access_count,
        },
    )

    # Load family member — use first name only for privacy
    member_result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == passport.member_id)
    )
    member = member_result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport data unavailable",
        )

    first_name = (member.full_name or "").split()[0] if member.full_name else "Unknown"
    flags = _sections_to_flags(passport.visible_sections or [])

    # Load health data respecting show_* visibility flags
    allergies: list[str] = []
    if flags["show_allergies"]:
        allergy_rows = (
            await db.execute(
                select(Allergy).where(Allergy.member_id == passport.member_id)
            )
        ).scalars().all()
        allergies = [a.allergen_name for a in allergy_rows]

    medications: list[dict] = []
    if flags["show_medications"]:
        med_rows = (
            await db.execute(
                select(Medication)
                .where(Medication.member_id == passport.member_id)
                .order_by(Medication.is_active.desc())
            )
        ).scalars().all()
        medications = [
            {"drug": m.drug_name, "dosage": m.dosage, "active": m.is_active}
            for m in med_rows
        ]

    diagnoses: list[str] = []
    if flags["show_diagnoses"]:
        diag_rows = (
            await db.execute(
                select(Diagnosis).where(Diagnosis.member_id == passport.member_id)
            )
        ).scalars().all()
        diagnoses = [d.condition_name for d in diag_rows]

    return PublicPassportResponse(
        passport_id=str(passport.passport_id),
        member_name=first_name,
        blood_group=member.blood_group,
        allergies=allergies,
        medications=medications,
        diagnoses=diagnoses,
        generated_at=now,
        expires_at=passport.expires_at,
    )
