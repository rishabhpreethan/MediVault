"""Onboarding endpoints — MV-151."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.allergy import Allergy
from app.models.family_member import FamilyMember
from app.models.provider_profile import ProviderProfile
from app.schemas.onboarding import (
    OnboardingCompleteResponse,
    OnboardingRequest,
    OnboardingStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: CurrentUser,
) -> OnboardingStatusResponse:
    """Return whether the authenticated user has completed onboarding."""
    return OnboardingStatusResponse(
        onboarding_completed=current_user.onboarding_completed,
        role=current_user.role,
    )


@router.post("", response_model=OnboardingCompleteResponse, status_code=200)
async def complete_onboarding(
    body: OnboardingRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> OnboardingCompleteResponse:
    """Save onboarding data and mark the user as onboarded.

    - Updates the self FamilyMember with DOB, blood_group, height_cm, weight_kg.
    - Creates manual Allergy entities for each allergy supplied.
    - Sets users.role and users.onboarding_completed = TRUE.
    - If role=PROVIDER: upserts a provider_profiles row and queues NMC verification.
    """
    if body.role == "PROVIDER" and not body.licence_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="licence_number is required for PROVIDER role",
        )

    # 1. Find self FamilyMember
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == current_user.user_id,
            FamilyMember.is_self == True,  # noqa: E712
        )
    )
    self_member = result.scalar_one_or_none()

    if self_member is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Self member not found — run /auth/provision first",
        )

    # 2. Update self member fields
    if body.full_name is not None and body.full_name.strip():
        self_member.full_name = body.full_name.strip()
    if body.date_of_birth is not None:
        self_member.date_of_birth = body.date_of_birth
    if body.height_cm is not None:
        self_member.height_cm = body.height_cm
    if body.weight_kg is not None:
        self_member.weight_kg = body.weight_kg
    if body.blood_group is not None:
        self_member.blood_group = body.blood_group

    # 3. Create allergy entities (skip duplicates by allergen_name)
    if body.allergies:
        existing_result = await db.execute(
            select(Allergy.allergen_name).where(
                Allergy.member_id == self_member.member_id,
                Allergy.allergen_name.in_(body.allergies),
            )
        )
        existing_names = {row[0] for row in existing_result.fetchall()}

        for allergen in body.allergies:
            if allergen.strip() and allergen not in existing_names:
                db.add(
                    Allergy(
                        member_id=self_member.member_id,
                        allergen_name=allergen.strip(),
                        is_manual_entry=True,
                        confidence_score="HIGH",
                    )
                )

    # 4. Update user role and mark onboarding complete
    current_user.role = body.role
    current_user.onboarding_completed = True

    # 5. Handle provider profile
    if body.role == "PROVIDER":
        provider_result = await db.execute(
            select(ProviderProfile).where(ProviderProfile.user_id == current_user.user_id)
        )
        provider_profile = provider_result.scalar_one_or_none()

        if provider_profile is None:
            provider_profile = ProviderProfile(
                user_id=current_user.user_id,
                licence_number=body.licence_number,
                registration_council=body.registration_council,
                verification_status="PENDING",
            )
            db.add(provider_profile)
        else:
            provider_profile.licence_number = body.licence_number
            provider_profile.registration_council = body.registration_council
            provider_profile.verification_status = "PENDING"
            provider_profile.licence_verified = False

        await db.flush()

        # Queue NMC verification (best-effort)
        try:
            from app.workers.onboarding_tasks import verify_licence_task  # noqa: PLC0415
            verify_licence_task.delay(
                str(current_user.user_id),
                body.licence_number,
                body.registration_council or "",
            )
            logger.info("Licence verification queued for user_id=%s", current_user.user_id)
        except Exception:
            logger.warning("Could not queue licence verification for user_id=%s", current_user.user_id)

    await db.commit()
    logger.info("Onboarding completed for user_id=%s role=%s", current_user.user_id, body.role)

    return OnboardingCompleteResponse(
        message="Onboarding complete",
        role=body.role,
        onboarding_completed=True,
    )
