"""Integration-style cross-vault isolation tests for MV-140.

Verifies that require_vault_access and the invite acceptance endpoint correctly
enforce ownership/grant boundaries — no live database required.

All tests use pytest + AsyncMock to simulate DB behaviour.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Stub heavy transitive dependencies before any app imports
# ---------------------------------------------------------------------------

if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

for _mod_name in ("boto3", "aioboto3", "botocore", "botocore.exceptions"):
    if _mod_name not in sys.modules:
        _stub = ModuleType(_mod_name)
        if _mod_name == "botocore.exceptions":
            _stub.ClientError = Exception  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _stub

# ---------------------------------------------------------------------------
# App imports (after stubs are in place)
# ---------------------------------------------------------------------------

from app.api.family_circle import accept_invite, create_access_grant
from app.dependencies import require_vault_access
from app.models.family_circle import (
    Family,
    FamilyInvitation,
    FamilyMembership,
    VaultAccessGrant,
)
from app.schemas.family_circle import CreateGrantRequest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_user(
    user_id: uuid.UUID | None = None,
    email: str = "test@example.com",
) -> MagicMock:
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    user.email = email
    return user


def _make_family_member_orm(
    member_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> MagicMock:
    from app.models.family_member import FamilyMember

    m = MagicMock(spec=FamilyMember)
    m.member_id = member_id or uuid.uuid4()
    m.user_id = user_id or uuid.uuid4()
    m.full_name = "Test User"
    m.relationship = "self"
    m.is_self = True
    return m


def _make_grant(
    grant_id: uuid.UUID | None = None,
    family_id: uuid.UUID | None = None,
    grantee_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
) -> MagicMock:
    grant = MagicMock(spec=VaultAccessGrant)
    grant.grant_id = grant_id or uuid.uuid4()
    grant.family_id = family_id or uuid.uuid4()
    grant.grantee_user_id = grantee_user_id or uuid.uuid4()
    grant.target_user_id = target_user_id or uuid.uuid4()
    grant.access_type = "READ"
    grant.granted_by_user_id = uuid.uuid4()
    grant.granted_at = _utcnow()
    return grant


def _make_invitation(
    invitation_id: uuid.UUID | None = None,
    family_id: uuid.UUID | None = None,
    invited_by_user_id: uuid.UUID | None = None,
    invited_email: str = "invitee@example.com",
    invited_user_id: uuid.UUID | None = None,
    relationship: str = "sibling",
    status: str = "PENDING",
    expires_at: datetime | None = None,
    token: uuid.UUID | None = None,
) -> MagicMock:
    inv = MagicMock(spec=FamilyInvitation)
    inv.invitation_id = invitation_id or uuid.uuid4()
    inv.family_id = family_id or uuid.uuid4()
    inv.invited_by_user_id = invited_by_user_id or uuid.uuid4()
    inv.invited_email = invited_email
    inv.invited_user_id = invited_user_id
    inv.relationship = relationship
    inv.status = status
    inv.token = token or uuid.uuid4()
    inv.expires_at = expires_at if expires_at is not None else (_utcnow() + timedelta(days=7))
    inv.created_at = _utcnow()
    return inv


def _make_membership(
    membership_id: uuid.UUID | None = None,
    family_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    role: str = "MEMBER",
) -> MagicMock:
    mem = MagicMock(spec=FamilyMembership)
    mem.membership_id = membership_id or uuid.uuid4()
    mem.family_id = family_id or uuid.uuid4()
    mem.user_id = user_id or uuid.uuid4()
    mem.role = role
    mem.can_invite = False
    mem.joined_at = _utcnow()
    return mem


def _mock_db() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _scalar_result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _scalars_result(rows: list) -> MagicMock:
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result = MagicMock()
    result.scalars.return_value = scalars_mock
    return result


# ---------------------------------------------------------------------------
# Test group 1: require_vault_access — ownership and grant rules
# ---------------------------------------------------------------------------


class TestRequireVaultAccessOwnership:
    """Owner of a member always has access; non-owner without grant is denied."""

    @pytest.mark.asyncio
    async def test_owner_can_always_access_own_member(self):
        """require_vault_access passes when member.user_id == current_user.user_id."""
        user = _make_user()
        member = _make_family_member_orm(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        # Must not raise
        await require_vault_access(
            member_id=member.member_id,
            current_user=user,
            db=db,
        )

    @pytest.mark.asyncio
    async def test_non_owner_without_grant_gets_403(self):
        """require_vault_access raises 403 when no grant exists and user is not owner."""
        owner = _make_user(email="owner@example.com")
        stranger = _make_user(email="stranger@example.com")
        member = _make_family_member_orm(user_id=owner.user_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(None),    # VaultAccessGrant → not found
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=member.member_id,
                current_user=stranger,
                db=db,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_grantee_with_read_grant_can_access_target(self):
        """require_vault_access passes when a VaultAccessGrant row exists for grantee→target."""
        owner = _make_user(email="owner@example.com")
        grantee = _make_user(email="grantee@example.com")
        member = _make_family_member_orm(user_id=owner.user_id)
        grant = _make_grant(
            grantee_user_id=grantee.user_id,
            target_user_id=owner.user_id,
        )

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(grant),   # VaultAccessGrant → found
            ]
        )

        # Must not raise
        await require_vault_access(
            member_id=member.member_id,
            current_user=grantee,
            db=db,
        )

    @pytest.mark.asyncio
    async def test_revoked_grant_no_longer_allows_access(self):
        """After a grant is deleted (DB returns None), 403 is raised."""
        owner = _make_user(email="owner@example.com")
        former_grantee = _make_user(email="former@example.com")
        member = _make_family_member_orm(user_id=owner.user_id)

        db = _mock_db()
        # Grant no longer in DB (simulates post-revocation state)
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(None),    # VaultAccessGrant → gone after revocation
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=member.member_id,
                current_user=former_grantee,
                db=db,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_grant_for_different_target_does_not_help(self):
        """A grant targeting user A does not grant access to user B's member vault."""
        user_a = _make_user(email="a@example.com")
        user_b = _make_user(email="b@example.com")
        grantee = _make_user(email="grantee@example.com")

        # Member belongs to user_b
        member_b = _make_family_member_orm(user_id=user_b.user_id)

        # Grant exists for grantee→user_a, NOT user_b
        grant_for_a = _make_grant(
            grantee_user_id=grantee.user_id,
            target_user_id=user_a.user_id,  # wrong target
        )

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member_b),   # load FamilyMember (user_b's member)
                _scalar_result(None),        # no grant for grantee→user_b
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=member_b.member_id,
                current_user=grantee,
                db=db,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_grant_for_different_grantee_does_not_help(self):
        """A grant where grantee_user_id != current_user does not allow access."""
        owner = _make_user(email="owner@example.com")
        correct_grantee = _make_user(email="correct@example.com")
        wrong_user = _make_user(email="wrong@example.com")
        member = _make_family_member_orm(user_id=owner.user_id)

        # Grant exists for correct_grantee but wrong_user is calling
        # DB correctly returns None because the WHERE filters on grantee_user_id=wrong_user
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(None),    # no grant for wrong_user→owner
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=member.member_id,
                current_user=wrong_user,
                db=db,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_member_not_found_raises_404(self):
        """require_vault_access raises 404 when the FamilyMember row does not exist."""
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test group 2: Invitation lifecycle isolation
# ---------------------------------------------------------------------------


class TestInvitationLifecycleIsolation:
    """Cross-cutting invite flow isolation tests — accept, expiry, double-accept."""

    @pytest.mark.asyncio
    async def test_expired_invitation_does_not_create_membership(self):
        """accept endpoint rejects expired invitation with HTTP 410."""
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
            expires_at=_utcnow() - timedelta(hours=1),  # expired
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 410
        # Confirm no membership was created
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_double_accept_rejected_with_409(self):
        """Accepting an already-accepted invitation returns 409."""
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="ACCEPTED",  # already consumed
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_accept_invite_wrong_user_gets_403(self):
        """Accepting an invite sent to a different email gives 403."""
        user = _make_user(email="different@example.com")
        inv = _make_invitation(
            invited_email="target@example.com",
            invited_user_id=uuid.uuid4(),  # also a different user_id
            status="PENDING",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_accept_invite_creates_membership_with_member_role(self):
        """Accepted invite creates FamilyMembership with role=MEMBER and can_invite=False."""
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
        )
        db = _mock_db()

        added: list = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))
        db.refresh = AsyncMock()

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(inv),  # _resolve_invitation_by_token
                _scalar_result(None), # existing membership check → none
            ]
        )

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            await accept_invite(token=inv.token, current_user=user, db=db)

        memberships = [o for o in added if isinstance(o, FamilyMembership)]
        assert len(memberships) == 1
        assert memberships[0].role == "MEMBER"
        assert memberships[0].can_invite is False

    @pytest.mark.asyncio
    async def test_accept_invite_already_member_returns_409(self):
        """Accepting an invite when already a family member raises 409."""
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
        )
        existing_membership = _make_membership(
            family_id=inv.family_id,
            user_id=user.user_id,
        )
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(inv),               # _resolve_invitation_by_token
                _scalar_result(existing_membership), # already a member
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test group 3: Non-member cannot create vault access grant
# ---------------------------------------------------------------------------


class TestNonMemberCannotCreateVaultAccessGrant:
    """Only family admins (creator or ADMIN member) can create vault access grants."""

    @pytest.mark.asyncio
    async def test_non_member_without_family_gets_404(self):
        """User with no family at all gets 404 when trying to create a grant."""
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))  # no family

        body = CreateGrantRequest(
            grantee_user_id=uuid.uuid4(),
            target_user_id=uuid.uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_access_grant(body=body, current_user=user, db=db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_non_admin_member_gets_403_on_create_grant(self):
        """A regular MEMBER (not ADMIN, not creator) gets 403 when creating a grant."""
        creator = _make_user(email="creator@example.com")
        regular_member = _make_user(email="member@example.com")
        family = _make_family(created_by_user_id=creator.user_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),  # _get_family_for_user → found
                _scalar_result(None),    # _require_admin: no ADMIN membership for regular_member
            ]
        )

        body = CreateGrantRequest(
            grantee_user_id=uuid.uuid4(),
            target_user_id=uuid.uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_access_grant(body=body, current_user=regular_member, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_family_creator_can_create_grant(self):
        """The family creator (is also admin) can successfully create a vault access grant."""
        creator = _make_user(email="creator@example.com")
        grantee_id = uuid.uuid4()
        target_id = uuid.uuid4()
        family = _make_family(created_by_user_id=creator.user_id)
        grantee_membership = _make_membership(family_id=family.family_id, user_id=grantee_id)
        target_membership = _make_membership(family_id=family.family_id, user_id=target_id)

        db = _mock_db()

        created_objects: list = []
        db.add = MagicMock(side_effect=lambda obj: created_objects.append(obj))
        db.refresh = AsyncMock()

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),             # _get_family_for_user
                _scalar_result(grantee_membership), # grantee check
                _scalar_result(target_membership),  # target check
            ]
        )

        body = CreateGrantRequest(
            grantee_user_id=grantee_id,
            target_user_id=target_id,
        )

        await create_access_grant(body=body, current_user=creator, db=db)

        grants = [o for o in created_objects if isinstance(o, VaultAccessGrant)]
        assert len(grants) == 1
        assert grants[0].grantee_user_id == grantee_id
        assert grants[0].target_user_id == target_id

    @pytest.mark.asyncio
    async def test_create_grant_returns_422_when_grantee_not_family_member(self):
        """Creating a grant for a grantee who is not in the family returns 422."""
        creator = _make_user(email="creator@example.com")
        family = _make_family(created_by_user_id=creator.user_id)
        non_member_id = uuid.uuid4()

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),  # _get_family_for_user
                _scalar_result(None),    # grantee membership → not found
            ]
        )

        body = CreateGrantRequest(
            grantee_user_id=non_member_id,
            target_user_id=uuid.uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_access_grant(body=body, current_user=creator, db=db)

        assert exc_info.value.status_code == 422
