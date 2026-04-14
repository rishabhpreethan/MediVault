"""Unit tests for the family members API business logic (MV-091).

Tests exercise the helper functions and route handlers directly without
using TestClient (greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

# Stub heavy dependencies before any app imports
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()
    sys.modules["spacy"] = _fake_spacy

for _mod in ("boto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        _fake = ModuleType(_mod)
        if _mod == "botocore.exceptions":
            _fake.ClientError = Exception
        sys.modules[_mod] = _fake

from app.api.family import (
    _load_member_or_404,
    _member_to_response,
    create_member,
    delete_member,
    get_member,
    list_members,
    update_member,
)
from app.schemas.family import FamilyMemberCreate, FamilyMemberUpdate


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
    relationship: str = "spouse",
    date_of_birth: date | None = date(1990, 5, 15),
    blood_group: str | None = "O+",
):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    member.full_name = full_name
    member.relationship = relationship
    member.date_of_birth = date_of_birth
    member.blood_group = blood_group
    member.is_self = False
    member.created_at = datetime.now(tz=timezone.utc)
    return member


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
# Tests: _load_member_or_404
# ---------------------------------------------------------------------------


class TestLoadMemberOr404:
    @pytest.mark.asyncio
    async def test_returns_member_when_owner(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        result = await _load_member_or_404(db, member.member_id, user)

        assert result is member

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await _load_member_or_404(db, uuid.uuid4(), user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403_when_wrong_owner(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())  # different user
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await _load_member_or_404(db, member.member_id, user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# test_create_member_sets_user_id
# ---------------------------------------------------------------------------


class TestCreateMember:
    @pytest.mark.asyncio
    async def test_create_member_sets_user_id(self):
        user = _make_user()
        db = _mock_db()

        captured: list = []

        def capture_add(obj):
            captured.append(obj)

        db.add = MagicMock(side_effect=capture_add)

        # db.refresh sets server_default fields on the real object
        async def mock_refresh(obj):
            if not getattr(obj, "created_at", None):
                obj.created_at = datetime.now(tz=timezone.utc)

        db.refresh = AsyncMock(side_effect=mock_refresh)

        body = FamilyMemberCreate(name="John Smith", relationship="parent")

        response = await create_member(body=body, current_user=user, db=db)

        db.add.assert_called_once()
        db.commit.assert_called()

        added_member = captured[0]
        assert added_member.user_id == user.user_id
        assert added_member.full_name == "John Smith"
        assert added_member.relationship == "parent"
        assert response.user_id == str(user.user_id)
        assert response.name == "John Smith"

    @pytest.mark.asyncio
    async def test_create_member_optional_fields_default_to_none(self):
        user = _make_user()
        db = _mock_db()

        captured: list = []
        db.add = MagicMock(side_effect=lambda obj: captured.append(obj))

        async def mock_refresh(obj):
            obj.created_at = datetime.now(tz=timezone.utc)

        db.refresh = AsyncMock(side_effect=mock_refresh)

        body = FamilyMemberCreate(name="Solo Member", relationship="self")

        response = await create_member(body=body, current_user=user, db=db)

        added_member = captured[0]
        assert added_member.date_of_birth is None
        assert added_member.blood_group is None
        assert response.date_of_birth is None
        assert response.blood_group is None


# ---------------------------------------------------------------------------
# test_list_members_returns_only_current_user_members
# ---------------------------------------------------------------------------


class TestListMembers:
    @pytest.mark.asyncio
    async def test_list_members_returns_only_current_user_members(self):
        user = _make_user()
        member1 = _make_member(user_id=user.user_id, full_name="Alice")
        member2 = _make_member(user_id=user.user_id, full_name="Bob")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_scalars_result([member1, member2]))

        response = await list_members(current_user=user, db=db)

        assert len(response) == 2
        names = {r.name for r in response}
        assert names == {"Alice", "Bob"}
        for r in response:
            assert r.user_id == str(user.user_id)

    @pytest.mark.asyncio
    async def test_list_members_returns_empty_list_when_none(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_scalars_result([]))

        response = await list_members(current_user=user, db=db)

        assert response == []


# ---------------------------------------------------------------------------
# test_get_member_raises_403_for_wrong_user
# ---------------------------------------------------------------------------


class TestGetMember:
    @pytest.mark.asyncio
    async def test_get_member_raises_403_for_wrong_user(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())  # owned by someone else
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_member(member_id=member.member_id, current_user=user, db=db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_member_returns_member_for_owner(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id, full_name="Carol")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        response = await get_member(member_id=member.member_id, current_user=user, db=db)

        assert response.name == "Carol"
        assert response.user_id == str(user.user_id)


# ---------------------------------------------------------------------------
# test_patch_updates_only_provided_fields
# ---------------------------------------------------------------------------


class TestUpdateMember:
    @pytest.mark.asyncio
    async def test_patch_updates_only_provided_fields(self):
        user = _make_user()
        member = _make_member(
            user_id=user.user_id,
            full_name="Original Name",
            relationship="sibling",
            blood_group="A+",
        )
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        async def mock_refresh(obj):
            pass

        db.refresh = AsyncMock(side_effect=mock_refresh)

        # Only updating blood_group — name and relationship should stay the same
        body = FamilyMemberUpdate(blood_group="B-")

        response = await update_member(
            member_id=member.member_id, body=body, current_user=user, db=db
        )

        # blood_group was updated on the member object
        assert member.blood_group == "B-"
        # full_name was NOT overwritten
        assert member.full_name == "Original Name"
        # relationship was NOT overwritten
        assert member.relationship == "sibling"
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_patch_raises_403_for_wrong_user(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        body = FamilyMemberUpdate(relationship="parent")

        with pytest.raises(HTTPException) as exc_info:
            await update_member(
                member_id=member.member_id, body=body, current_user=user, db=db
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_updates_name_via_full_name_mapping(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id, full_name="Old Name")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))
        db.refresh = AsyncMock()

        body = FamilyMemberUpdate(name="New Name")

        await update_member(member_id=member.member_id, body=body, current_user=user, db=db)

        assert member.full_name == "New Name"


# ---------------------------------------------------------------------------
# test_delete_calls_db_delete
# ---------------------------------------------------------------------------


class TestDeleteMember:
    @pytest.mark.asyncio
    async def test_delete_calls_db_delete(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        await delete_member(member_id=member.member_id, current_user=user, db=db)

        db.delete.assert_called_once_with(member)
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_raises_403_for_wrong_user(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await delete_member(member_id=member.member_id, current_user=user, db=db)

        assert exc_info.value.status_code == 403
        db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_raises_404_when_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await delete_member(member_id=uuid.uuid4(), current_user=user, db=db)

        assert exc_info.value.status_code == 404
        db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_raises_409_when_is_self(self):
        """MV-146: the user's own self-member cannot be deleted."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        member.is_self = True  # mark as self-member
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await delete_member(member_id=member.member_id, current_user=user, db=db)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"] == "CANNOT_DELETE_SELF"
        db.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: _member_to_response
# ---------------------------------------------------------------------------


class TestMemberToResponse:
    def test_converts_uuids_to_strings(self):
        member = _make_member()
        response = _member_to_response(member)

        assert isinstance(response.member_id, str)
        assert isinstance(response.user_id, str)
        assert str(member.member_id) == response.member_id
        assert str(member.user_id) == response.user_id

    def test_maps_full_name_to_name(self):
        member = _make_member(full_name="Test Patient")
        response = _member_to_response(member)

        assert response.name == "Test Patient"

    def test_gender_is_always_none(self):
        member = _make_member()
        response = _member_to_response(member)

        assert response.gender is None

    def test_optional_fields_preserved(self):
        member = _make_member(
            date_of_birth=date(1985, 3, 22),
            blood_group="AB-",
        )
        response = _member_to_response(member)

        assert response.date_of_birth == date(1985, 3, 22)
        assert response.blood_group == "AB-"

    def test_optional_fields_none_when_not_set(self):
        member = _make_member(date_of_birth=None, blood_group=None)
        response = _member_to_response(member)

        assert response.date_of_birth is None
        assert response.blood_group is None
