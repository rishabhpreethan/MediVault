"""Family Circle API — MV-126 through MV-129.

Endpoints:
  GET    /family/circle
  POST   /family/invitations
  GET    /family/invitations
  DELETE /family/invitations/{invitation_id}
  POST   /family/invitations/{invitation_id}/resend
  GET    /invite/{token}            (public)
  POST   /invite/{token}/accept
  POST   /invite/{token}/decline
  GET    /family/access
  POST   /family/access
  DELETE /family/access/{grant_id}
  PATCH  /family/memberships/{membership_id}/can-invite
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select

from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.models.family_circle import (
    Family,
    FamilyInvitation,
    FamilyMembership,
    VaultAccessGrant,
)
from app.models.family_member import FamilyMember
from app.models.user import User
from app.schemas.family import FamilyMemberResponse
from app.schemas.family_circle import (
    CreateGrantRequest,
    FamilyCircleResponse,
    FamilyInvitationResponse,
    FamilyMembershipResponse,
    FamilyResponse,
    InviteTokenResponse,
    SendInvitationRequest,
    ToggleCanInviteRequest,
    VaultAccessGrantResponse,
)
from app.services.notification_service import dispatch_notification

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _family_to_response(f: Family) -> FamilyResponse:
    return FamilyResponse(
        family_id=f.family_id,
        name=f.name,
        created_by_user_id=f.created_by_user_id,
        created_at=f.created_at,
    )


def _invitation_to_response(inv: FamilyInvitation) -> FamilyInvitationResponse:
    return FamilyInvitationResponse(
        invitation_id=inv.invitation_id,
        family_id=inv.family_id,
        invited_by_user_id=inv.invited_by_user_id,
        invited_email=inv.invited_email,
        invited_user_id=inv.invited_user_id,
        relationship=inv.relationship,
        status=inv.status,
        token=inv.token,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
    )


def _membership_to_response(m: FamilyMembership) -> FamilyMembershipResponse:
    return FamilyMembershipResponse(
        membership_id=m.membership_id,
        family_id=m.family_id,
        user_id=m.user_id,
        role=m.role,
        can_invite=m.can_invite,
        joined_at=m.joined_at,
    )


def _grant_to_response(g: VaultAccessGrant) -> VaultAccessGrantResponse:
    return VaultAccessGrantResponse(
        grant_id=g.grant_id,
        family_id=g.family_id,
        grantee_user_id=g.grantee_user_id,
        target_user_id=g.target_user_id,
        access_type=g.access_type,
        granted_by_user_id=g.granted_by_user_id,
        granted_at=g.granted_at,
    )


def _member_to_response(m: FamilyMember) -> FamilyMemberResponse:
    return FamilyMemberResponse(
        member_id=str(m.member_id),
        user_id=str(m.user_id),
        full_name=m.full_name,
        name=m.full_name,
        relationship=m.relationship,
        date_of_birth=m.date_of_birth,
        blood_group=m.blood_group,
        gender=None,
        is_self=m.is_self,
        created_at=m.created_at,
    )


async def _get_family_for_user(
    db: DbSession,
    user_id: uuid.UUID,
) -> Family | None:
    result = await db.execute(
        select(Family).where(Family.created_by_user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _require_admin(
    db: DbSession,
    family: Family,
    current_user,
) -> None:
    """Raise 403 if current_user is not an admin of the family."""
    if family.created_by_user_id == current_user.user_id:
        return
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.family_id == family.family_id,
            FamilyMembership.user_id == current_user.user_id,
            FamilyMembership.role == "ADMIN",
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Admin access required"},
        )


async def _resolve_invitation_by_token(
    db: DbSession,
    token: uuid.UUID,
) -> FamilyInvitation:
    result = await db.execute(
        select(FamilyInvitation).where(FamilyInvitation.token == token)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Invitation not found"},
        )
    return inv


# ---------------------------------------------------------------------------
# MV-126: GET /family/circle
# ---------------------------------------------------------------------------


@router.get("/family/circle", response_model=FamilyCircleResponse)
async def get_family_circle(
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyCircleResponse:
    """Return the full family circle snapshot for the authenticated user."""
    # Family owned by this user
    family = await _get_family_for_user(db, current_user.user_id)

    # Self member (separate from managed_profiles)
    self_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == current_user.user_id,
            FamilyMember.is_self == True,  # noqa: E712
        )
    )
    self_member_row = self_result.scalar_one_or_none()
    self_member_resp = _member_to_response(self_member_row) if self_member_row else None

    # Managed profiles: non-self FamilyMember rows owned by this user
    fm_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == current_user.user_id,
            FamilyMember.is_self == False,  # noqa: E712
        )
    )
    managed = [_member_to_response(m) for m in fm_result.scalars().all()]

    # Memberships (families this user has joined via invite)
    mem_result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == current_user.user_id
        )
    )
    memberships = [_membership_to_response(m) for m in mem_result.scalars().all()]

    # Pending invitations sent by this user
    if family:
        sent_result = await db.execute(
            select(FamilyInvitation).where(
                FamilyInvitation.family_id == family.family_id,
                FamilyInvitation.invited_by_user_id == current_user.user_id,
                FamilyInvitation.status == "PENDING",
            )
        )
        sent = [_invitation_to_response(i) for i in sent_result.scalars().all()]
    else:
        sent = []

    # Pending invitations received by this user (by user_id OR by email)
    recv_result = await db.execute(
        select(FamilyInvitation).where(
            FamilyInvitation.status == "PENDING",
            or_(
                FamilyInvitation.invited_user_id == current_user.user_id,
                FamilyInvitation.invited_email == current_user.email,
            ),
        )
    )
    received = [_invitation_to_response(i) for i in recv_result.scalars().all()]

    return FamilyCircleResponse(
        family=_family_to_response(family) if family else None,
        self_member=self_member_resp,
        managed_profiles=managed,
        memberships=memberships,
        pending_invitations_sent=sent,
        pending_invitations_received=received,
    )


# ---------------------------------------------------------------------------
# MV-127: POST /family/invitations
# ---------------------------------------------------------------------------


@router.post(
    "/family/invitations",
    response_model=FamilyInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_invitation(
    body: SendInvitationRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyInvitationResponse:
    """Send a family invitation to an email address."""
    # Cannot invite yourself
    if current_user.email and body.email.lower() == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "SELF_INVITE", "message": "Cannot invite yourself"},
        )

    # Auto-create family if needed
    family = await _get_family_for_user(db, current_user.user_id)
    if family is None:
        family = Family(
            family_id=uuid.uuid4(),
            name=f"{current_user.email or str(current_user.user_id)}'s Family",
            created_by_user_id=current_user.user_id,
        )
        db.add(family)
        await db.flush()
        logger.info(
            "family_auto_created",
            extra={"family_id": str(family.family_id), "user_id": str(current_user.user_id)},
        )

    # Check for existing PENDING invitation for this email in this family
    existing_result = await db.execute(
        select(FamilyInvitation).where(
            FamilyInvitation.family_id == family.family_id,
            FamilyInvitation.invited_email == body.email.lower(),
            FamilyInvitation.status == "PENDING",
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "INVITATION_PENDING", "message": "Invitation already pending"},
        )

    # Resolve invited_user_id if the email belongs to an existing user
    invited_user_id: uuid.UUID | None = None
    user_lookup = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    invited_user = user_lookup.scalar_one_or_none()
    if invited_user is not None:
        invited_user_id = invited_user.user_id

    invitation = FamilyInvitation(
        invitation_id=uuid.uuid4(),
        family_id=family.family_id,
        invited_by_user_id=current_user.user_id,
        invited_email=body.email.lower(),
        invited_user_id=invited_user_id,
        relationship=body.relationship,
        status="PENDING",
        token=uuid.uuid4(),
        expires_at=_utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    await db.flush()

    # Dispatch in-app notification if invited user exists
    if invited_user_id is not None:
        inviter_name = current_user.email or str(current_user.user_id)
        await dispatch_notification(
            db=db,
            user_id=invited_user_id,
            type="FAMILY_INVITE",
            title=f"Family invitation from {inviter_name}",
            body=(
                f"{inviter_name} has invited you to join their family as "
                f"{body.relationship}."
            ),
            action_url=f"/invite/{invitation.token}",
            metadata={"invitation_id": str(invitation.invitation_id)},
        )

    await db.commit()
    await db.refresh(invitation)

    # Send invite email — best-effort, never blocks the response
    try:
        from app.services.email_service import send_family_invite_email  # noqa: PLC0415
        frontend_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
        inviter_display = current_user.email or str(current_user.user_id)
        send_family_invite_email(
            to=body.email.lower(),
            inviter_name=inviter_display,
            relationship=body.relationship,
            accept_url=f"{frontend_url}/invite/{invitation.token}",
            app_url=frontend_url,
        )
    except Exception as exc:
        logger.warning("invite_email_failed", extra={"error": str(exc)})

    logger.info(
        "invitation_sent",
        extra={
            "invitation_id": str(invitation.invitation_id),
            "family_id": str(family.family_id),
            "invited_by_user_id": str(current_user.user_id),
        },
    )
    return _invitation_to_response(invitation)


# ---------------------------------------------------------------------------
# MV-127: GET /family/invitations
# ---------------------------------------------------------------------------


@router.get("/family/invitations", response_model=list[FamilyInvitationResponse])
async def list_invitations(
    current_user: CurrentUser,
    db: DbSession,
) -> list[FamilyInvitationResponse]:
    """List invitations sent by the current user within their family."""
    family = await _get_family_for_user(db, current_user.user_id)
    if family is None:
        return []

    result = await db.execute(
        select(FamilyInvitation).where(
            FamilyInvitation.family_id == family.family_id,
            FamilyInvitation.invited_by_user_id == current_user.user_id,
        ).order_by(FamilyInvitation.created_at.desc())
    )
    return [_invitation_to_response(i) for i in result.scalars().all()]


# ---------------------------------------------------------------------------
# MV-127: DELETE /family/invitations/{invitation_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/family/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def cancel_invitation(
    invitation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Cancel a PENDING invitation (only the sender can cancel)."""
    result = await db.execute(
        select(FamilyInvitation).where(FamilyInvitation.invitation_id == invitation_id)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Invitation not found"},
        )
    if inv.invited_by_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Access denied"},
        )
    if inv.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "NOT_PENDING",
                "message": "Only PENDING invitations can be cancelled",
            },
        )
    inv.status = "REVOKED"
    await db.commit()
    logger.info(
        "invitation_cancelled",
        extra={
            "invitation_id": str(invitation_id),
            "user_id": str(current_user.user_id),
        },
    )


# ---------------------------------------------------------------------------
# MV-127: POST /family/invitations/{invitation_id}/resend
# ---------------------------------------------------------------------------


@router.post(
    "/family/invitations/{invitation_id}/resend",
    response_model=FamilyInvitationResponse,
)
async def resend_invitation(
    invitation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyInvitationResponse:
    """Extend a PENDING invitation by 7 days and resend the notification."""
    result = await db.execute(
        select(FamilyInvitation).where(FamilyInvitation.invitation_id == invitation_id)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Invitation not found"},
        )
    if inv.invited_by_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Access denied"},
        )
    if inv.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "NOT_PENDING",
                "message": "Only PENDING invitations can be resent",
            },
        )

    inv.expires_at = inv.expires_at + timedelta(days=7)

    if inv.invited_user_id is not None:
        inviter_name = current_user.email or str(current_user.user_id)
        await dispatch_notification(
            db=db,
            user_id=inv.invited_user_id,
            type="FAMILY_INVITE",
            title=f"Family invitation from {inviter_name}",
            body=(
                f"{inviter_name} has invited you to join their family as "
                f"{inv.relationship}."
            ),
            action_url=f"/invite/{inv.token}",
            metadata={"invitation_id": str(inv.invitation_id)},
        )

    await db.commit()
    await db.refresh(inv)

    # Resend email — best-effort
    try:
        from app.services.email_service import send_family_invite_email  # noqa: PLC0415
        frontend_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
        inviter_display = current_user.email or str(current_user.user_id)
        send_family_invite_email(
            to=inv.invited_email,
            inviter_name=inviter_display,
            relationship=inv.relationship,
            accept_url=f"{frontend_url}/invite/{inv.token}",
            app_url=frontend_url,
        )
    except Exception as exc:
        logger.warning("invite_resend_email_failed", extra={"error": str(exc)})

    logger.info(
        "invitation_resent",
        extra={
            "invitation_id": str(invitation_id),
            "user_id": str(current_user.user_id),
        },
    )
    return _invitation_to_response(inv)


# ---------------------------------------------------------------------------
# MV-128: GET /invite/{token}  (public — no auth)
# ---------------------------------------------------------------------------


@router.get("/invite/{token}", response_model=InviteTokenResponse)
async def resolve_invite_token(
    token: uuid.UUID,
    db: DbSession,
) -> InviteTokenResponse:
    """Public endpoint — resolve an invite token and return safe invitation details."""
    inv = await _resolve_invitation_by_token(db, token)

    if inv.status == "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "ALREADY_ACCEPTED", "message": "Invitation already accepted"},
        )
    if inv.status in ("DECLINED", "REVOKED", "EXPIRED"):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "INVITATION_INACTIVE", "message": "Invitation is no longer active"},
        )
    if inv.expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "INVITATION_EXPIRED", "message": "Invitation has expired"},
        )

    # Fetch inviter name (email) — do not expose PII beyond display name
    inviter_result = await db.execute(
        select(User).where(User.user_id == inv.invited_by_user_id)
    )
    inviter = inviter_result.scalar_one_or_none()
    inviter_name = inviter.email if inviter else None

    return InviteTokenResponse(
        invitation_id=inv.invitation_id,
        family_id=inv.family_id,
        relationship=inv.relationship,
        status=inv.status,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
        inviter_name=inviter_name,
    )


# ---------------------------------------------------------------------------
# MV-128: POST /invite/{token}/accept
# ---------------------------------------------------------------------------


@router.post("/invite/{token}/accept", response_model=FamilyMembershipResponse)
async def accept_invite(
    token: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyMembershipResponse:
    """Accept a family invitation — creates a FamilyMembership."""
    inv = await _resolve_invitation_by_token(db, token)

    if inv.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "NOT_PENDING", "message": "Invitation is no longer pending"},
        )
    if inv.expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "INVITATION_EXPIRED", "message": "Invitation has expired"},
        )

    # Confirm the accepting user matches the invitation
    email_match = (
        current_user.email is not None
        and inv.invited_email.lower() == current_user.email.lower()
    )
    user_id_match = inv.invited_user_id == current_user.user_id
    if not (email_match or user_id_match):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "This invitation was not sent to you"},
        )

    # Check not already a member
    existing_mem = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.family_id == inv.family_id,
            FamilyMembership.user_id == current_user.user_id,
        )
    )
    if existing_mem.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "ALREADY_MEMBER", "message": "You are already a member of this family"},
        )

    membership = FamilyMembership(
        membership_id=uuid.uuid4(),
        family_id=inv.family_id,
        user_id=current_user.user_id,
        role="MEMBER",
        can_invite=False,
    )
    db.add(membership)

    inv.status = "ACCEPTED"
    # Ensure invited_user_id is set for future reference
    if inv.invited_user_id is None:
        inv.invited_user_id = current_user.user_id

    await db.flush()

    # Notify the inviter
    accepter_name = current_user.email or str(current_user.user_id)
    await dispatch_notification(
        db=db,
        user_id=inv.invited_by_user_id,
        type="INVITE_ACCEPTED",
        title=f"{accepter_name} accepted your family invitation",
        body=f"{accepter_name} has joined your family.",
        action_url="/family/circle",
        metadata={"invitation_id": str(inv.invitation_id)},
    )

    await db.commit()
    await db.refresh(membership)

    logger.info(
        "invitation_accepted",
        extra={
            "invitation_id": str(inv.invitation_id),
            "membership_id": str(membership.membership_id),
            "user_id": str(current_user.user_id),
        },
    )
    return _membership_to_response(membership)


# ---------------------------------------------------------------------------
# MV-128: POST /invite/{token}/decline
# ---------------------------------------------------------------------------


@router.post("/invite/{token}/decline", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def decline_invite(
    token: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Decline a family invitation."""
    inv = await _resolve_invitation_by_token(db, token)

    if inv.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "NOT_PENDING", "message": "Invitation is no longer pending"},
        )

    email_match = (
        current_user.email is not None
        and inv.invited_email.lower() == current_user.email.lower()
    )
    user_id_match = inv.invited_user_id == current_user.user_id
    if not (email_match or user_id_match):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "This invitation was not sent to you"},
        )

    inv.status = "DECLINED"
    await db.flush()

    # Notify the inviter
    decliner_name = current_user.email or str(current_user.user_id)
    await dispatch_notification(
        db=db,
        user_id=inv.invited_by_user_id,
        type="INVITE_DECLINED",
        title=f"{decliner_name} declined your family invitation",
        body=f"{decliner_name} has declined your family invitation.",
        action_url="/family/circle",
        metadata={"invitation_id": str(inv.invitation_id)},
    )

    await db.commit()
    logger.info(
        "invitation_declined",
        extra={
            "invitation_id": str(inv.invitation_id),
            "user_id": str(current_user.user_id),
        },
    )


# ---------------------------------------------------------------------------
# MV-129: GET /family/access
# ---------------------------------------------------------------------------


@router.get("/family/access", response_model=list[VaultAccessGrantResponse])
async def list_access_grants(
    current_user: CurrentUser,
    db: DbSession,
) -> list[VaultAccessGrantResponse]:
    """List all vault access grants for the current user's family (admin only)."""
    family = await _get_family_for_user(db, current_user.user_id)
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_FAMILY", "message": "You have not created a family yet"},
        )
    await _require_admin(db, family, current_user)

    result = await db.execute(
        select(VaultAccessGrant).where(VaultAccessGrant.family_id == family.family_id)
    )
    return [_grant_to_response(g) for g in result.scalars().all()]


# ---------------------------------------------------------------------------
# MV-129: POST /family/access
# ---------------------------------------------------------------------------


@router.post(
    "/family/access",
    response_model=VaultAccessGrantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_access_grant(
    body: CreateGrantRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> VaultAccessGrantResponse:
    """Create a vault access grant (admin only; both users must be family members)."""
    family = await _get_family_for_user(db, current_user.user_id)
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_FAMILY", "message": "You have not created a family yet"},
        )
    await _require_admin(db, family, current_user)

    # Verify grantee is a family member
    grantee_check = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.family_id == family.family_id,
            FamilyMembership.user_id == body.grantee_user_id,
        )
    )
    if grantee_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "GRANTEE_NOT_MEMBER",
                "message": "Grantee is not a member of this family",
            },
        )

    # Verify target is a family member OR is the family creator
    target_is_creator = body.target_user_id == family.created_by_user_id
    if not target_is_creator:
        target_check = await db.execute(
            select(FamilyMembership).where(
                FamilyMembership.family_id == family.family_id,
                FamilyMembership.user_id == body.target_user_id,
            )
        )
        if target_check.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "TARGET_NOT_MEMBER",
                    "message": "Target user is not a member of this family",
                },
            )

    grant = VaultAccessGrant(
        grant_id=uuid.uuid4(),
        family_id=family.family_id,
        grantee_user_id=body.grantee_user_id,
        target_user_id=body.target_user_id,
        access_type="READ",
        granted_by_user_id=current_user.user_id,
    )
    db.add(grant)
    await db.commit()
    await db.refresh(grant)

    logger.info(
        "vault_access_grant_created",
        extra={
            "grant_id": str(grant.grant_id),
            "family_id": str(family.family_id),
            "granted_by_user_id": str(current_user.user_id),
        },
    )
    return _grant_to_response(grant)


# ---------------------------------------------------------------------------
# MV-129: DELETE /family/access/{grant_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/family/access/{grant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def revoke_access_grant(
    grant_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Revoke a vault access grant (admin only)."""
    result = await db.execute(
        select(VaultAccessGrant).where(VaultAccessGrant.grant_id == grant_id)
    )
    grant = result.scalar_one_or_none()
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Access grant not found"},
        )

    # Load family to check admin access
    family_result = await db.execute(
        select(Family).where(Family.family_id == grant.family_id)
    )
    family = family_result.scalar_one_or_none()
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Family not found"},
        )
    await _require_admin(db, family, current_user)

    await db.delete(grant)
    await db.commit()
    logger.info(
        "vault_access_grant_revoked",
        extra={"grant_id": str(grant_id), "user_id": str(current_user.user_id)},
    )


# ---------------------------------------------------------------------------
# MV-129: PATCH /family/memberships/{membership_id}/can-invite
# ---------------------------------------------------------------------------


@router.patch(
    "/family/memberships/{membership_id}/can-invite",
    response_model=FamilyMembershipResponse,
)
async def toggle_can_invite(
    membership_id: uuid.UUID,
    body: ToggleCanInviteRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> FamilyMembershipResponse:
    """Toggle the can_invite flag on a family membership (admin only)."""
    result = await db.execute(
        select(FamilyMembership).where(FamilyMembership.membership_id == membership_id)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Membership not found"},
        )

    family_result = await db.execute(
        select(Family).where(Family.family_id == membership.family_id)
    )
    family = family_result.scalar_one_or_none()
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Family not found"},
        )
    await _require_admin(db, family, current_user)

    membership.can_invite = body.can_invite
    await db.commit()
    await db.refresh(membership)

    logger.info(
        "membership_can_invite_toggled",
        extra={
            "membership_id": str(membership_id),
            "can_invite": body.can_invite,
            "user_id": str(current_user.user_id),
        },
    )
    return _membership_to_response(membership)
