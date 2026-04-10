"""Unit tests for the Health Passport API (MV-080).

Tests exercise route handlers directly without TestClient
(greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.passport import (
    _passport_to_response,
    _sections_to_flags,
    create_passport,
    list_passports,
    revoke_passport,
    view_public_passport,
)
from app.schemas.passport import PassportCreate


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: uuid.UUID | None = None):
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    return user


def _make_member(
    user_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    full_name: str = "Jane Doe",
    blood_group: str | None = "O+",
):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    member.full_name = full_name
    member.blood_group = blood_group
    return member


def _make_passport(
    passport_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    is_active: bool = True,
    expires_at: datetime | None = None,
    visible_sections: list | None = None,
    access_count: int = 0,
):
    from app.models.passport import SharedPassport

    passport = MagicMock(spec=SharedPassport)
    passport.passport_id = passport_id or uuid.uuid4()
    passport.member_id = member_id or uuid.uuid4()
    passport.user_id = user_id or uuid.uuid4()
    passport.is_active = is_active
    passport.expires_at = expires_at or (datetime.now(tz=timezone.utc) + timedelta(days=30))
    passport.visible_sections = visible_sections if visible_sections is not None else [
        "medications", "labs", "diagnoses", "allergies"
    ]
    passport.access_count = access_count
    passport.created_at = datetime.now(tz=timezone.utc)
    return passport


def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _db_scalars_result(values: list):
    scalars = MagicMock()
    scalars.all.return_value = values
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


# ---------------------------------------------------------------------------
# Tests: create_passport
# ---------------------------------------------------------------------------


class TestCreatePassport:
    @pytest.mark.asyncio
    async def test_create_passport_sets_share_token_and_expiry(self):
        """Newly created passport has share_token (== passport_id) and expires_at set."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        captured: list = []

        def capture_add(obj):
            captured.append(obj)
            # Simulate server-defaults set after add
            obj.passport_id = uuid.uuid4()
            obj.created_at = datetime.now(tz=timezone.utc)
            obj.access_count = 0

        db.add = MagicMock(side_effect=capture_add)
        db.execute = AsyncMock(return_value=_db_result(member))

        async def mock_refresh(obj):
            pass

        db.refresh = AsyncMock(side_effect=mock_refresh)

        body = PassportCreate(member_id=str(member.member_id), expires_in_days=10)

        response = await create_passport(body=body, current_user=user, db=db)

        assert response.share_token is not None
        assert response.share_token == response.passport_id
        assert response.expires_at is not None
        assert response.is_active is True

    @pytest.mark.asyncio
    async def test_create_passport_404_member_not_found(self):
        """Creating a passport for a non-existent member raises 404."""
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        body = PassportCreate(member_id=str(uuid.uuid4()), expires_in_days=30)

        with pytest.raises(HTTPException) as exc_info:
            await create_passport(body=body, current_user=user, db=db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_passport_403_wrong_user(self):
        """Creating a passport for another user's member raises 403."""
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())  # owned by someone else
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        body = PassportCreate(member_id=str(member.member_id), expires_in_days=30)

        with pytest.raises(HTTPException) as exc_info:
            await create_passport(body=body, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_passport_default_visibility_all_true(self):
        """Default PassportCreate has all show_* flags True."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        captured: list = []

        def capture_add(obj):
            captured.append(obj)
            obj.passport_id = uuid.uuid4()
            obj.created_at = datetime.now(tz=timezone.utc)
            obj.access_count = 0

        db.add = MagicMock(side_effect=capture_add)
        db.execute = AsyncMock(return_value=_db_result(member))
        db.refresh = AsyncMock()

        body = PassportCreate(member_id=str(member.member_id))

        response = await create_passport(body=body, current_user=user, db=db)

        assert response.show_medications is True
        assert response.show_labs is True
        assert response.show_diagnoses is True
        assert response.show_allergies is True


# ---------------------------------------------------------------------------
# Tests: list_passports
# ---------------------------------------------------------------------------


class TestListPassports:
    @pytest.mark.asyncio
    async def test_list_passports_returns_only_member_passports(self):
        """List endpoint returns passports for the given member."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        p1 = _make_passport(member_id=member.member_id)
        p2 = _make_passport(member_id=member.member_id)
        db = _mock_db()

        # first execute loads the member, second loads passports
        db.execute = AsyncMock(
            side_effect=[
                _db_result(member),
                _db_scalars_result([p1, p2]),
            ]
        )

        response = await list_passports(member_id=member.member_id, current_user=user, db=db)

        assert response.total == 2
        assert len(response.items) == 2

    @pytest.mark.asyncio
    async def test_list_passports_empty_when_none(self):
        """List endpoint returns empty list when no passports exist."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(member),
                _db_scalars_result([]),
            ]
        )

        response = await list_passports(member_id=member.member_id, current_user=user, db=db)

        assert response.total == 0
        assert response.items == []


# ---------------------------------------------------------------------------
# Tests: revoke_passport
# ---------------------------------------------------------------------------


class TestRevokePassport:
    @pytest.mark.asyncio
    async def test_revoke_passport_sets_inactive(self):
        """Revoking a passport sets is_active to False."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        passport = _make_passport(member_id=member.member_id, user_id=user.user_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(passport),   # load passport
                _db_result(member),     # load member for ownership check
            ]
        )

        await revoke_passport(passport_id=passport.passport_id, current_user=user, db=db)

        assert passport.is_active is False
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_passport_404(self):
        """Revoking a non-existent passport raises 404."""
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await revoke_passport(passport_id=uuid.uuid4(), current_user=user, db=db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_passport_403_wrong_user(self):
        """Revoking another user's passport raises 403."""
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)
        passport = _make_passport(member_id=member.member_id, user_id=other_user_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(passport),
                _db_result(member),
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await revoke_passport(passport_id=passport.passport_id, current_user=user, db=db)

        assert exc_info.value.status_code == 403
        assert passport.is_active is True  # not changed


# ---------------------------------------------------------------------------
# Tests: view_public_passport
# ---------------------------------------------------------------------------


class TestPublicPassport:
    @pytest.mark.asyncio
    async def test_public_view_returns_data(self):
        """Public endpoint returns passport data when valid."""
        member_id = uuid.uuid4()
        passport = _make_passport(member_id=member_id)
        member = _make_member(member_id=member_id, full_name="John Smith", blood_group="A+")
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(passport),            # load passport
                _db_result(member),              # load member
                _db_scalars_result([]),          # allergies
                _db_scalars_result([]),          # medications
                _db_scalars_result([]),          # diagnoses
            ]
        )

        response = await view_public_passport(share_token=passport.passport_id, db=db)

        assert response.passport_id == str(passport.passport_id)
        assert response.member_name == "John"  # first name only
        assert response.blood_group == "A+"
        assert response.disclaimer != ""

    @pytest.mark.asyncio
    async def test_public_view_respects_visibility_flags(self):
        """show_medications=False results in empty medications list."""
        member_id = uuid.uuid4()
        # Only allergies and diagnoses visible — no medications, no labs
        passport = _make_passport(
            member_id=member_id,
            visible_sections=["allergies", "diagnoses"],
        )
        member = _make_member(member_id=member_id)

        from app.models.allergy import Allergy
        from app.models.diagnosis import Diagnosis

        allergy = MagicMock(spec=Allergy)
        allergy.allergen_name = "Penicillin"

        diag = MagicMock(spec=Diagnosis)
        diag.condition_name = "Hypertension"

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result(passport),
                _db_result(member),
                _db_scalars_result([allergy]),   # allergies — visible
                _db_scalars_result([diag]),      # diagnoses — visible
            ]
        )

        response = await view_public_passport(share_token=passport.passport_id, db=db)

        assert response.medications == []      # show_medications=False
        assert "Penicillin" in response.allergies
        assert "Hypertension" in response.diagnoses

    @pytest.mark.asyncio
    async def test_public_view_404_invalid_token(self):
        """Invalid share_token returns 404."""
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await view_public_passport(share_token=uuid.uuid4(), db=db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_public_view_410_expired(self):
        """Expired passport returns 410 GONE."""
        member_id = uuid.uuid4()
        past = datetime.now(tz=timezone.utc) - timedelta(days=1)
        passport = _make_passport(member_id=member_id, is_active=True, expires_at=past)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(passport))

        with pytest.raises(HTTPException) as exc_info:
            await view_public_passport(share_token=passport.passport_id, db=db)

        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_public_view_410_revoked(self):
        """Revoked (is_active=False) passport returns 410 GONE."""
        member_id = uuid.uuid4()
        passport = _make_passport(member_id=member_id, is_active=False)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(passport))

        with pytest.raises(HTTPException) as exc_info:
            await view_public_passport(share_token=passport.passport_id, db=db)

        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_public_view_increments_access_count(self):
        """Successful public access increments access_count."""
        member_id = uuid.uuid4()
        passport = _make_passport(member_id=member_id, access_count=5)
        member = _make_member(member_id=member_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(passport),
                _db_result(member),
                _db_scalars_result([]),
                _db_scalars_result([]),
                _db_scalars_result([]),
            ]
        )

        await view_public_passport(share_token=passport.passport_id, db=db)

        assert passport.access_count == 6
        db.commit.assert_called()


# ---------------------------------------------------------------------------
# Tests: helper functions
# ---------------------------------------------------------------------------


class TestSectionsToFlags:
    def test_all_sections_present(self):
        flags = _sections_to_flags(["medications", "labs", "diagnoses", "allergies"])
        assert flags["show_medications"] is True
        assert flags["show_labs"] is True
        assert flags["show_diagnoses"] is True
        assert flags["show_allergies"] is True

    def test_empty_sections(self):
        flags = _sections_to_flags([])
        assert flags["show_medications"] is False
        assert flags["show_labs"] is False
        assert flags["show_diagnoses"] is False
        assert flags["show_allergies"] is False

    def test_partial_sections(self):
        flags = _sections_to_flags(["medications"])
        assert flags["show_medications"] is True
        assert flags["show_labs"] is False
        assert flags["show_diagnoses"] is False
        assert flags["show_allergies"] is False


class TestPassportToResponse:
    def test_share_token_equals_passport_id(self):
        passport = _make_passport()
        response = _passport_to_response(passport)
        assert response.share_token == response.passport_id
        assert response.share_token == str(passport.passport_id)
