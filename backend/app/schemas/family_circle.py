"""Pydantic v2 schemas for the Family Circle API."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.family import FamilyMemberResponse


class FamilyResponse(BaseModel):
    family_id: uuid.UUID
    name: str
    created_by_user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyInvitationResponse(BaseModel):
    invitation_id: uuid.UUID
    family_id: uuid.UUID
    invited_by_user_id: uuid.UUID
    invited_email: str
    invited_user_id: Optional[uuid.UUID] = None
    relationship: str
    status: str
    token: uuid.UUID
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyMembershipResponse(BaseModel):
    membership_id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    can_invite: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class VaultAccessGrantResponse(BaseModel):
    grant_id: uuid.UUID
    family_id: uuid.UUID
    grantee_user_id: uuid.UUID
    target_user_id: uuid.UUID
    access_type: str
    granted_by_user_id: uuid.UUID
    granted_at: datetime

    model_config = {"from_attributes": True}


class FamilyCircleResponse(BaseModel):
    family: Optional[FamilyResponse] = None
    self_member: Optional[FamilyMemberResponse] = None
    managed_profiles: list[FamilyMemberResponse]
    memberships: list[FamilyMembershipResponse]
    pending_invitations_sent: list[FamilyInvitationResponse]
    pending_invitations_received: list[FamilyInvitationResponse]

    model_config = {"from_attributes": True}


class SendInvitationRequest(BaseModel):
    email: str
    relationship: str


class CreateGrantRequest(BaseModel):
    grantee_user_id: uuid.UUID
    target_user_id: uuid.UUID


class ToggleCanInviteRequest(BaseModel):
    can_invite: bool


class InviteTokenResponse(BaseModel):
    """Public (no auth) view of an invitation — no sensitive user info."""
    invitation_id: uuid.UUID
    family_id: uuid.UUID
    relationship: str
    status: str
    expires_at: datetime
    created_at: datetime
    # Inviter display name provided separately by the route, not from DB
    inviter_name: Optional[str] = None

    model_config = {"from_attributes": True}
