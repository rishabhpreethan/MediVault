"""Unit tests for Family Circle API and notification service (MV-139).

Covers:
- notification_service.dispatch_notification
- Family invitation logic (POST, DELETE)
- Invite acceptance and decline
- Vault access grant admin checks
- require_vault_access dependency (cross-vault middleware)
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

from app.api.family_circle import (
    accept_invite,
    cancel_invitation,
    create_access_grant,
    decline_invite,
    revoke_access_grant,
    send_invitation,
)
from app.dependencies import require_vault_access
from app.models.family_circle import (
    Family,
    FamilyInvitation,
    FamilyMembership,
    VaultAccessGrant,
)
from app.models.notification import Notification
from app.schemas.family_circle import CreateGrantRequest, SendInvitationRequest
from app.services.notification_service import dispatch_notification


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_user(
    user_id: uuid.UUID | None = None,
    email: str = "test@example.com",
):
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    user.email = email
    return user


def _make_family(
    family_id: uuid.UUID | None = None,
    created_by_user_id: uuid.UUID | None = None,
) -> MagicMock:
    family = MagicMock(spec=Family)
    family.family_id = family_id or uuid.uuid4()
    family.created_by_user_id = created_by_user_id or uuid.uuid4()
    family.name = "Test Family"
    family.created_at = _utcnow()
    return family


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
    can_invite: bool = False,
) -> MagicMock:
    mem = MagicMock(spec=FamilyMembership)
    mem.membership_id = membership_id or uuid.uuid4()
    mem.family_id = family_id or uuid.uuid4()
    mem.user_id = user_id or uuid.uuid4()
    mem.role = role
    mem.can_invite = can_invite
    mem.joined_at = _utcnow()
    return mem


def _make_grant(
    grant_id: uuid.UUID | None = None,
    family_id: uuid.UUID | None = None,
    grantee_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    granted_by_user_id: uuid.UUID | None = None,
) -> MagicMock:
    grant = MagicMock(spec=VaultAccessGrant)
    grant.grant_id = grant_id or uuid.uuid4()
    grant.family_id = family_id or uuid.uuid4()
    grant.grantee_user_id = grantee_user_id or uuid.uuid4()
    grant.target_user_id = target_user_id or uuid.uuid4()
    grant.access_type = "READ"
    grant.granted_by_user_id = granted_by_user_id or uuid.uuid4()
    grant.granted_at = _utcnow()
    return grant


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
# 1. Notification dispatch service
# ---------------------------------------------------------------------------


class TestDispatchNotification:
    """Unit tests for notification_service.dispatch_notification."""

    @pytest.mark.asyncio
    async def test_dispatch_notification_creates_notification_with_correct_fields(self):
        db = _mock_db()
        user_id = uuid.uuid4()

        result = await dispatch_notification(
            db=db,
            user_id=user_id,
            type="FAMILY_INVITE",
            title="You have been invited",
            body="Someone invited you.",
            action_url="/invite/abc",
            metadata={"invitation_id": "abc"},
        )

        assert isinstance(result, Notification)
        assert result.user_id == user_id
        assert result.type == "FAMILY_INVITE"
        assert result.title == "You have been invited"
        assert result.body == "Someone invited you."
        assert result.action_url == "/invite/abc"
        assert result.extra_data == {"invitation_id": "abc"}

    @pytest.mark.asyncio
    async def test_dispatch_notification_calls_db_add(self):
        db = _mock_db()

        await dispatch_notification(
            db=db,
            user_id=uuid.uuid4(),
            type="INVITE_ACCEPTED",
            title="Accepted",
            body="Your invite was accepted.",
        )

        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert isinstance(added_obj, Notification)

    @pytest.mark.asyncio
    async def test_dispatch_notification_calls_db_flush(self):
        db = _mock_db()

        await dispatch_notification(
            db=db,
            user_id=uuid.uuid4(),
            type="INVITE_DECLINED",
            title="Declined",
            body="Your invite was declined.",
        )

        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_notification_returns_notification_instance(self):
        db = _mock_db()

        notif = await dispatch_notification(
            db=db,
            user_id=uuid.uuid4(),
            type="FAMILY_INVITE",
            title="Test",
            body="Test body",
        )

        assert isinstance(notif, Notification)

    @pytest.mark.asyncio
    async def test_dispatch_notification_optional_fields_default_to_none(self):
        db = _mock_db()

        notif = await dispatch_notification(
            db=db,
            user_id=uuid.uuid4(),
            type="FAMILY_INVITE",
            title="No extras",
            body="No extras body",
            # action_url and metadata intentionally omitted
        )

        assert notif.action_url is None
        assert notif.extra_data is None


# ---------------------------------------------------------------------------
# 2. Family invitation logic
# ---------------------------------------------------------------------------


class TestSendInvitation:
    """POST /family/invitations — business logic unit tests."""

    @pytest.mark.asyncio
    async def test_send_invitation_auto_creates_family_when_none_exists(self):
        user = _make_user(email="owner@example.com")
        db = _mock_db()

        created_objects: list = []

        def capture_add(obj):
            created_objects.append(obj)

        db.add = MagicMock(side_effect=capture_add)

        async def mock_refresh(obj):
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = _utcnow()
            if not hasattr(obj, "expires_at") or obj.expires_at is None:
                obj.expires_at = _utcnow() + timedelta(days=7)
            obj.invited_user_id = None

        db.refresh = AsyncMock(side_effect=mock_refresh)

        # First execute → no family; second execute → no pending invite; third → no existing user
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(None),  # _get_family_for_user → no family
                _scalar_result(None),  # existing pending invitation check → none
                _scalar_result(None),  # user lookup by email → not found
            ]
        )

        body = SendInvitationRequest(email="invitee@example.com", relationship="sibling")

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            await send_invitation(body=body, current_user=user, db=db)

        family_objs = [o for o in created_objects if isinstance(o, Family)]
        assert len(family_objs) == 1
        assert family_objs[0].created_by_user_id == user.user_id

    @pytest.mark.asyncio
    async def test_send_invitation_returns_409_when_pending_invite_exists(self):
        user = _make_user()
        family = _make_family(created_by_user_id=user.user_id)
        existing_inv = _make_invitation(
            family_id=family.family_id,
            invited_email="invitee@example.com",
            status="PENDING",
        )
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),       # _get_family_for_user → found
                _scalar_result(existing_inv), # pending invitation check → found
            ]
        )

        body = SendInvitationRequest(email="invitee@example.com", relationship="sibling")

        with pytest.raises(HTTPException) as exc_info:
            await send_invitation(body=body, current_user=user, db=db)

        assert exc_info.value.status_code == 409
        assert "INVITATION_PENDING" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_invitation_returns_400_when_self_invite(self):
        user = _make_user(email="me@example.com")
        db = _mock_db()

        body = SendInvitationRequest(email="me@example.com", relationship="self")

        with pytest.raises(HTTPException) as exc_info:
            await send_invitation(body=body, current_user=user, db=db)

        assert exc_info.value.status_code == 400
        assert "SELF_INVITE" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_invitation_sets_invited_user_id_when_email_matches_existing_user(self):
        user = _make_user(email="owner@example.com")
        family = _make_family(created_by_user_id=user.user_id)
        existing_invitee = _make_user(email="invitee@example.com")
        db = _mock_db()

        created_objects: list = []
        db.add = MagicMock(side_effect=lambda obj: created_objects.append(obj))

        async def mock_refresh(obj):
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = _utcnow()
            if isinstance(obj, FamilyInvitation):
                pass  # attributes already set on real object

        db.refresh = AsyncMock(side_effect=mock_refresh)

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),          # _get_family_for_user → found
                _scalar_result(None),             # pending invitation check → none
                _scalar_result(existing_invitee), # user lookup by email → found
            ]
        )

        body = SendInvitationRequest(email="invitee@example.com", relationship="child")

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            await send_invitation(body=body, current_user=user, db=db)

        inv_objs = [o for o in created_objects if isinstance(o, FamilyInvitation)]
        assert len(inv_objs) == 1
        assert inv_objs[0].invited_user_id == existing_invitee.user_id


class TestCancelInvitation:
    """DELETE /family/invitations/{id} — business logic unit tests."""

    @pytest.mark.asyncio
    async def test_cancel_invitation_sets_status_revoked(self):
        user = _make_user()
        inv = _make_invitation(invited_by_user_id=user.user_id, status="PENDING")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        await cancel_invitation(invitation_id=inv.invitation_id, current_user=user, db=db)

        assert inv.status == "REVOKED"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_invitation_returns_403_when_not_sender(self):
        user = _make_user()
        other_user = _make_user()
        inv = _make_invitation(invited_by_user_id=other_user.user_id, status="PENDING")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await cancel_invitation(invitation_id=inv.invitation_id, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_invitation_returns_404_when_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await cancel_invitation(invitation_id=uuid.uuid4(), current_user=user, db=db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_invitation_returns_409_when_not_pending(self):
        user = _make_user()
        inv = _make_invitation(invited_by_user_id=user.user_id, status="ACCEPTED")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await cancel_invitation(invitation_id=inv.invitation_id, current_user=user, db=db)

        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 3. Invite acceptance and decline
# ---------------------------------------------------------------------------


class TestAcceptInvite:
    """POST /invite/{token}/accept — business logic unit tests."""

    @pytest.mark.asyncio
    async def test_accept_invite_creates_family_membership_with_correct_fields(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_by_user_id=uuid.uuid4(),
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
        )
        db = _mock_db()

        created_objects: list = []
        db.add = MagicMock(side_effect=lambda obj: created_objects.append(obj))

        async def mock_refresh(obj):
            if not hasattr(obj, "joined_at") or obj.joined_at is None:
                obj.joined_at = _utcnow()

        db.refresh = AsyncMock(side_effect=mock_refresh)

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(inv),  # _resolve_invitation_by_token
                _scalar_result(None), # existing membership check → none
            ]
        )

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            result = await accept_invite(token=inv.token, current_user=user, db=db)

        membership_objs = [o for o in created_objects if isinstance(o, FamilyMembership)]
        assert len(membership_objs) == 1
        assert membership_objs[0].family_id == inv.family_id
        assert membership_objs[0].user_id == user.user_id
        assert membership_objs[0].role == "MEMBER"
        assert membership_objs[0].can_invite is False

    @pytest.mark.asyncio
    async def test_accept_invite_returns_410_when_token_expired(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
            expires_at=_utcnow() - timedelta(days=1),  # expired
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_accept_invite_returns_409_when_already_accepted(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="ACCEPTED",  # already accepted
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        # NOT_PENDING triggers 409
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_accept_invite_returns_403_when_invitee_email_does_not_match(self):
        user = _make_user(email="wrong@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=uuid.uuid4(),  # different user_id too
            status="PENDING",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_accept_invite_sets_invitation_status_to_accepted(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="PENDING",
        )
        db = _mock_db()

        db.add = MagicMock()
        db.refresh = AsyncMock()

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(inv),  # _resolve_invitation_by_token
                _scalar_result(None), # existing membership check → none
            ]
        )

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            await accept_invite(token=inv.token, current_user=user, db=db)

        assert inv.status == "ACCEPTED"


class TestDeclineInvite:
    """POST /invite/{token}/decline — business logic unit tests."""

    @pytest.mark.asyncio
    async def test_decline_invite_sets_status_declined(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            invited_by_user_id=uuid.uuid4(),
            status="PENDING",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with patch("app.api.family_circle.dispatch_notification", new_callable=AsyncMock):
            await decline_invite(token=inv.token, current_user=user, db=db)

        assert inv.status == "DECLINED"

    @pytest.mark.asyncio
    async def test_decline_invite_returns_403_for_wrong_recipient(self):
        user = _make_user(email="wrong@example.com")
        inv = _make_invitation(
            invited_email="other@example.com",
            invited_user_id=uuid.uuid4(),
            status="PENDING",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await decline_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_decline_invite_returns_409_when_not_pending(self):
        user = _make_user(email="invitee@example.com")
        inv = _make_invitation(
            invited_email="invitee@example.com",
            invited_user_id=user.user_id,
            status="REVOKED",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(inv))

        with pytest.raises(HTTPException) as exc_info:
            await decline_invite(token=inv.token, current_user=user, db=db)

        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 4. Vault access grants — admin checks
# ---------------------------------------------------------------------------


class TestCreateAccessGrant:
    """POST /family/access — admin-only vault access grant creation."""

    @pytest.mark.asyncio
    async def test_create_grant_returns_403_for_non_admin_member(self):
        creator = _make_user()
        non_admin = _make_user()
        family = _make_family(created_by_user_id=creator.user_id)

        # non_admin is not the creator and has no ADMIN membership
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),  # _get_family_for_user → found
                _scalar_result(None),    # _require_admin: FamilyMembership ADMIN check → none
            ]
        )

        body = CreateGrantRequest(
            grantee_user_id=uuid.uuid4(),
            target_user_id=uuid.uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_access_grant(body=body, current_user=non_admin, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_grant_returns_404_when_no_family(self):
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
    async def test_create_grant_succeeds_for_family_creator(self):
        creator = _make_user()
        grantee_id = uuid.uuid4()
        target_id = uuid.uuid4()
        family = _make_family(created_by_user_id=creator.user_id)
        grantee_membership = _make_membership(family_id=family.family_id, user_id=grantee_id)
        target_membership = _make_membership(family_id=family.family_id, user_id=target_id)

        db = _mock_db()

        created_objects: list = []
        db.add = MagicMock(side_effect=lambda obj: created_objects.append(obj))

        async def mock_refresh(obj):
            obj.granted_at = _utcnow()

        db.refresh = AsyncMock(side_effect=mock_refresh)

        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(family),             # _get_family_for_user
                # creator.user_id == family.created_by_user_id → _require_admin returns early
                _scalar_result(grantee_membership), # grantee membership check
                _scalar_result(target_membership),  # target membership check
            ]
        )

        body = CreateGrantRequest(
            grantee_user_id=grantee_id,
            target_user_id=target_id,
        )

        await create_access_grant(body=body, current_user=creator, db=db)

        grant_objs = [o for o in created_objects if isinstance(o, VaultAccessGrant)]
        assert len(grant_objs) == 1
        assert grant_objs[0].grantee_user_id == grantee_id
        assert grant_objs[0].target_user_id == target_id
        assert grant_objs[0].granted_by_user_id == creator.user_id


class TestRevokeAccessGrant:
    """DELETE /family/access/{grant_id} — admin-only revocation."""

    @pytest.mark.asyncio
    async def test_revoke_grant_admin_can_delete_grant(self):
        admin = _make_user()
        family = _make_family(created_by_user_id=admin.user_id)
        grant = _make_grant(family_id=family.family_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(grant),   # load grant
                _scalar_result(family),  # load family
                # admin is creator → _require_admin returns early (no extra query)
            ]
        )

        await revoke_access_grant(grant_id=grant.grant_id, current_user=admin, db=db)

        db.delete.assert_called_once_with(grant)
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_grant_returns_403_for_non_admin(self):
        creator = _make_user()
        non_admin = _make_user()
        family = _make_family(created_by_user_id=creator.user_id)
        grant = _make_grant(family_id=family.family_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(grant),   # load grant
                _scalar_result(family),  # load family
                _scalar_result(None),    # _require_admin: ADMIN membership → none
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await revoke_access_grant(grant_id=grant.grant_id, current_user=non_admin, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_revoke_grant_returns_404_when_grant_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await revoke_access_grant(grant_id=uuid.uuid4(), current_user=user, db=db)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# 5. Cross-vault middleware (require_vault_access)
# ---------------------------------------------------------------------------


class TestRequireVaultAccess:
    """Unit tests for the require_vault_access dependency in dependencies.py."""

    @pytest.mark.asyncio
    async def test_owner_of_member_is_allowed(self):
        user = _make_user()
        member = _make_family_member_orm(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        # Should not raise
        await require_vault_access(
            member_id=member.member_id,
            current_user=user,
            db=db,
        )

    @pytest.mark.asyncio
    async def test_user_with_vault_access_grant_is_allowed(self):
        owner = _make_user()
        grantee = _make_user()
        member = _make_family_member_orm(user_id=owner.user_id)
        grant = _make_grant(
            grantee_user_id=grantee.user_id,
            target_user_id=owner.user_id,
        )
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(grant),   # load VaultAccessGrant
            ]
        )

        # Should not raise
        await require_vault_access(
            member_id=member.member_id,
            current_user=grantee,
            db=db,
        )

    @pytest.mark.asyncio
    async def test_user_with_no_grant_and_not_owner_raises_403(self):
        owner = _make_user()
        stranger = _make_user()
        member = _make_family_member_orm(user_id=owner.user_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),  # load FamilyMember
                _scalar_result(None),    # no VaultAccessGrant
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
    async def test_member_not_found_raises_404(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))  # member not found

        with pytest.raises(HTTPException) as exc_info:
            await require_vault_access(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404
