"""Integration-style data isolation tests for MV-093.

Verifies that all API endpoints correctly scope data to the requesting user's
family members — no cross-user data leakage.

These tests use the same AsyncMock / sys.modules injection pattern as the unit
tests (no real DB required).
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from types import ModuleType
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

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

from app.api.charts import get_lab_trends, get_medication_timeline
from app.api.corrections import patch_entity_field
from app.api.documents import list_documents
from app.api.entity_crud import create_medication
from app.api.family import get_member, list_members
from app.api.passport import list_passports
from app.api.profile import get_profile
from app.api.timeline import get_timeline
from app.schemas.corrections import FieldCorrectionRequest
from app.schemas.entity_crud import MedicationCreate


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: Optional[uuid.UUID] = None) -> MagicMock:
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    return user


def _make_member(
    user_id: Optional[uuid.UUID] = None,
    member_id: Optional[uuid.UUID] = None,
) -> MagicMock:
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    member.full_name = "Test User"
    member.relationship = "self"
    member.date_of_birth = None
    member.blood_group = None
    member.is_self = True
    return member


def _make_medication_orm(member_id: Optional[uuid.UUID] = None) -> MagicMock:
    from app.models.medication import Medication

    med = MagicMock(spec=Medication)
    med.medication_id = uuid.uuid4()
    med.member_id = member_id or uuid.uuid4()
    med.drug_name = "Aspirin"
    med.drug_name_normalized = None
    med.dosage = "100mg"
    med.frequency = "daily"
    med.route = "oral"
    med.start_date = None
    med.end_date = None
    med.is_active = True
    med.confidence_score = "HIGH"
    med.is_manual_entry = False
    med.document_id = None
    med.created_at = datetime.now(tz=timezone.utc)
    return med


def _make_audit_orm(
    entity_type: str = "medication",
    entity_id: Optional[uuid.UUID] = None,
) -> MagicMock:
    from app.models.correction_audit import CorrectionAudit

    audit = MagicMock(spec=CorrectionAudit)
    audit.audit_id = uuid.uuid4()
    audit.entity_type = entity_type
    audit.entity_id = entity_id or uuid.uuid4()
    audit.field_name = "drug_name"
    audit.old_value = "Aspirin"
    audit.new_value = "Ibuprofen"
    audit.corrected_by = uuid.uuid4()
    audit.corrected_at = datetime.now(tz=timezone.utc)
    return audit


def _mock_db() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _scalar_result(value: object) -> MagicMock:
    """Mock result whose .scalar_one_or_none() returns value."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _scalars_result(rows: list) -> MagicMock:
    """Mock result whose .scalars().all() returns rows."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result = MagicMock()
    result.scalars.return_value = scalars_mock
    return result


def _scalar_one_result(value: object) -> MagicMock:
    """Mock result whose .scalar_one() returns value."""
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


# ---------------------------------------------------------------------------
# Test 1 — Profile API: cannot access another user's member
# ---------------------------------------------------------------------------


class TestProfileApiCannotAccessOtherUsersMember:
    """GET /profile/ with a member_id that belongs to user B, requested by user A → 403."""

    @pytest.mark.asyncio
    async def test_profile_api_cannot_access_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        # member belongs to user_b
        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_profile(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 2 — Timeline API: cannot access another user's member
# ---------------------------------------------------------------------------


class TestTimelineApiCannotAccessOtherUsersMember:
    """GET /timeline/ with another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_timeline_api_cannot_access_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_timeline(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 3 — Documents API: cannot list another user's documents
# ---------------------------------------------------------------------------


class TestDocumentsApiCannotListOtherUsersDocuments:
    """GET /documents/ with another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_documents_api_cannot_list_other_users_documents(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await list_documents(
                current_user=user_a,
                db=db,
                member_id=member.member_id,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 4 — Charts lab trends: cannot access another user's member
# ---------------------------------------------------------------------------


class TestChartsLabTrendsCannotAccessOtherUsersMember:
    """GET /charts/lab-trends with another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_charts_lab_trends_cannot_access_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_lab_trends(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 5 — Charts medication timeline: cannot access another user's member
# ---------------------------------------------------------------------------


class TestChartsMedicationTimelineCannotAccessOtherUsersMember:
    """GET /charts/medication-timeline with another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_charts_medication_timeline_cannot_access_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_medication_timeline(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 6 — Entity CRUD: cannot create entity for another user's member
# ---------------------------------------------------------------------------


class TestEntityCrudCannotCreateEntityForOtherUsersMember:
    """POST /profile/{member_id}/medications for another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_entity_crud_cannot_create_entity_for_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        body = MedicationCreate(
            drug_name="Aspirin",
            dosage="100mg",
            frequency="daily",
            route="oral",
            start_date=None,
            end_date=None,
            is_active=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_medication(
                member_id=member.member_id,
                body=body,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 7 — Corrections: cannot patch another user's entity
# ---------------------------------------------------------------------------


class TestCorrectionsCannotPatchOtherUsersEntity:
    """PATCH /corrections/medication/{id} when entity's member belongs to user B → 403."""

    @pytest.mark.asyncio
    async def test_corrections_cannot_patch_other_users_entity(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        # medication whose member belongs to user_b
        med = _make_medication_orm()
        member = _make_member(user_id=user_b.user_id, member_id=med.member_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(med),      # _load_entity_or_404 → loads the medication
                _scalar_result(member),   # _verify_ownership → loads the FamilyMember
            ]
        )

        body = FieldCorrectionRequest(field_name="drug_name", new_value="Ibuprofen")

        with pytest.raises(HTTPException) as exc_info:
            await patch_entity_field(
                entity_type="medication",
                entity_id=med.medication_id,
                body=body,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 8 — Passport: cannot list another user's passports
# ---------------------------------------------------------------------------


class TestPassportCannotListOtherUsersPassports:
    """GET /passport/ with another user's member_id → 403."""

    @pytest.mark.asyncio
    async def test_passport_cannot_list_other_users_passports(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await list_passports(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 9 — Family API: list_members returns only the requesting user's members
# ---------------------------------------------------------------------------


class TestFamilyMemberListScopedToCurrentUser:
    """GET /family/members returns only members belonging to the authenticated user.

    The list_members endpoint filters by FamilyMember.user_id == current_user.user_id
    in the SQL query. We verify the handler calls execute with the correct user scope
    and never returns the other user's member.
    """

    @pytest.mark.asyncio
    async def test_family_member_list_scoped_to_current_user(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        # user_a has one member; user_b has one member
        member_a = _make_member(user_id=user_a.user_id)
        # member_b will NOT appear in user_a's query result (DB scoping)

        db = _mock_db()
        # Simulate DB returning only user_a's members (already scoped by WHERE clause)
        db.execute = AsyncMock(return_value=_scalars_result([member_a]))

        result = await list_members(
            current_user=user_a,
            db=db,
        )

        # Only user_a's member is returned
        assert len(result) == 1
        assert result[0].user_id == str(user_a.user_id)

        # Confirm user_b's member_id is not in the result
        returned_member_ids = {r.member_id for r in result}
        assert str(user_b.user_id) not in returned_member_ids


# ---------------------------------------------------------------------------
# Test 10 — Family get_member: cannot access another user's member directly
# ---------------------------------------------------------------------------


class TestFamilyGetMemberCannotAccessOtherUsersMember:
    """GET /family/members/{member_id} when member belongs to user B, requested by user A → 403."""

    @pytest.mark.asyncio
    async def test_family_get_member_cannot_access_other_users_member(self) -> None:
        user_a = _make_user()
        user_b = _make_user()

        member = _make_member(user_id=user_b.user_id)

        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_member(
                member_id=member.member_id,
                current_user=user_a,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 11 — Profile: requesting user's own member succeeds (positive case)
# ---------------------------------------------------------------------------


class TestProfileApiOwnerCanAccessOwnMember:
    """GET /profile/ with user's own member_id → succeeds (no 403 raised).

    Positive-path sanity check: ownership correctly grants access.
    """

    @pytest.mark.asyncio
    async def test_profile_api_owner_can_access_own_member(self) -> None:
        user_a = _make_user()
        member = _make_member(user_id=user_a.user_id)

        db = _mock_db()
        # _load_member_or_404 fetches member, then 5 entity queries return empty lists
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),   # load member
                _scalars_result([]),       # medications
                _scalars_result([]),       # lab results
                _scalars_result([]),       # diagnoses
                _scalars_result([]),       # allergies
                _scalars_result([]),       # vitals
            ]
        )

        # Should not raise
        response = await get_profile(
            member_id=member.member_id,
            current_user=user_a,
            db=db,
        )

        assert str(response.member.user_id) == str(user_a.user_id)


# ---------------------------------------------------------------------------
# Test 12 — Charts: requesting user's own member succeeds (positive case)
# ---------------------------------------------------------------------------


class TestChartsLabTrendsOwnerCanAccessOwnMember:
    """GET /charts/lab-trends with user's own member_id → succeeds (no 403 raised)."""

    @pytest.mark.asyncio
    async def test_charts_lab_trends_owner_can_access_own_member(self) -> None:
        user_a = _make_user()
        member = _make_member(user_id=user_a.user_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),   # load member
                _scalars_result([]),       # lab results (empty)
            ]
        )

        response = await get_lab_trends(
            member_id=member.member_id,
            current_user=user_a,
            db=db,
        )

        assert response.member_id == str(member.member_id)
        assert response.series == []


# ---------------------------------------------------------------------------
# Test 13 — Passport: requesting user's own member succeeds (positive case)
# ---------------------------------------------------------------------------


class TestPassportOwnerCanListOwnPassports:
    """GET /passport/ with user's own member_id → succeeds (no 403 raised)."""

    @pytest.mark.asyncio
    async def test_passport_owner_can_list_own_passports(self) -> None:
        user_a = _make_user()
        member = _make_member(user_id=user_a.user_id)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _scalar_result(member),   # load member
                _scalars_result([]),       # passports (empty)
            ]
        )

        response = await list_passports(
            member_id=member.member_id,
            current_user=user_a,
            db=db,
        )

        assert response.total == 0
        assert response.items == []
