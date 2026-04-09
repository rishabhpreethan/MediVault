"""Family members API — create, list, retrieve, update, and delete family members."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.family_member import FamilyMember
from app.schemas.family import FamilyMemberCreate, FamilyMemberResponse, FamilyMemberUpdate

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


def _member_to_response(member: FamilyMember) -> FamilyMemberResponse:
    """Convert a FamilyMember ORM row to a FamilyMemberResponse schema."""
    return FamilyMemberResponse(
        member_id=str(member.member_id),
        user_id=str(member.user_id),
        full_name=member.full_name,
        relationship=member.relationship,
        date_of_birth=member.date_of_birth,
        blood_group=member.blood_group,
        is_self=member.is_self,
    )


# ---------------------------------------------------------------------------
# POST /family/members
# ---------------------------------------------------------------------------


@router.post("/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    body: FamilyMemberCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyMemberResponse:
    """Create a new family member for the authenticated user."""
    member = FamilyMember(
        member_id=uuid.uuid4(),
        user_id=current_user.user_id,
        full_name=body.name,
        relationship=body.relationship,
        date_of_birth=body.date_of_birth,
        blood_group=body.blood_group,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    logger.info(
        "Family member created",
        extra={"member_id": str(member.member_id), "user_id": str(current_user.user_id)},
    )

    return _member_to_response(member)


# ---------------------------------------------------------------------------
# GET /family/members
# ---------------------------------------------------------------------------


@router.get("/members", response_model=list[FamilyMemberResponse])
async def list_members(
    current_user: CurrentUser,
    db: DbSession,
) -> list[FamilyMemberResponse]:
    """Return all family members for the authenticated user, ordered by created_at asc."""
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.user_id == current_user.user_id)
        .order_by(FamilyMember.created_at.asc())
    )
    members = result.scalars().all()
    return [_member_to_response(m) for m in members]


# ---------------------------------------------------------------------------
# GET /family/members/{member_id}
# ---------------------------------------------------------------------------


@router.get("/members/{member_id}", response_model=FamilyMemberResponse)
async def get_member(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyMemberResponse:
    """Return a single family member by ID (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)
    return _member_to_response(member)


# ---------------------------------------------------------------------------
# PATCH /family/members/{member_id}
# ---------------------------------------------------------------------------


@router.patch("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_member(
    member_id: uuid.UUID,
    body: FamilyMemberUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyMemberResponse:
    """Partially update a family member (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "name":
            member.full_name = value
        elif field == "gender":
            # gender is not stored on the model; silently ignore
            pass
        else:
            setattr(member, field, value)

    await db.commit()
    await db.refresh(member)

    logger.info(
        "Family member updated",
        extra={"member_id": str(member.member_id), "user_id": str(current_user.user_id)},
    )

    return _member_to_response(member)


# ---------------------------------------------------------------------------
# DELETE /family/members/{member_id}
# ---------------------------------------------------------------------------


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_member(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a family member and cascade all associated data (ownership verified)."""
    member = await _load_member_or_404(db, member_id, current_user)

    await db.delete(member)
    await db.commit()

    logger.info(
        "Family member deleted",
        extra={"member_id": str(member_id), "user_id": str(current_user.user_id)},
    )
