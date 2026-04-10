"""Unit tests for the Manual Field Correction API (MV-027).

Tests exercise route handlers directly without TestClient
(greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# Inject fake spacy so any transitive imports succeed without the real package.
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

# Inject fake boto3 / botocore so storage_service can be imported without the
# real packages installed locally.
if "boto3" not in sys.modules:
    _fake_boto3 = ModuleType("boto3")
    _fake_boto3.client = MagicMock()  # type: ignore[attr-defined]
    sys.modules["boto3"] = _fake_boto3
if "botocore" not in sys.modules:
    _fake_botocore = ModuleType("botocore")
    _fake_botocore_exc = ModuleType("botocore.exceptions")
    _fake_botocore_exc.ClientError = Exception  # type: ignore[attr-defined]
    sys.modules["botocore"] = _fake_botocore
    sys.modules["botocore.exceptions"] = _fake_botocore_exc

from app.api.corrections import get_correction_history, patch_entity_field
from app.schemas.corrections import FieldCorrectionRequest


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
):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    return member


def _make_lab_result(member_id: uuid.UUID | None = None, result_id: uuid.UUID | None = None):
    from app.models.lab_result import LabResult

    lab = MagicMock(spec=LabResult)
    lab.result_id = result_id or uuid.uuid4()
    lab.member_id = member_id or uuid.uuid4()
    lab.test_name = "Glucose"
    lab.value = "5.5"
    lab.unit = "mmol/L"
    lab.reference_range = "3.9-6.1"
    return lab


def _make_audit(entity_type: str = "lab_result", entity_id: uuid.UUID | None = None):
    from app.models.correction_audit import CorrectionAudit

    audit = MagicMock(spec=CorrectionAudit)
    audit.audit_id = uuid.uuid4()
    audit.entity_type = entity_type
    audit.entity_id = entity_id or uuid.uuid4()
    audit.field_name = "test_name"
    audit.old_value = "Glucose"
    audit.new_value = "Blood Glucose"
    audit.corrected_at = datetime.now(tz=timezone.utc)
    return audit


def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
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
# Tests: PATCH /corrections/{entity_type}/{entity_id}
# ---------------------------------------------------------------------------


class TestPatchEntityField:
    @pytest.mark.asyncio
    async def test_patch_lab_result_field_success(self):
        """Patching a valid lab_result field creates a CorrectionAudit and updates the entity."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        lab = _make_lab_result(member_id=member.member_id)
        db = _mock_db()

        captured_audits: list = []

        def capture_add(obj):
            from app.models.correction_audit import CorrectionAudit
            if isinstance(obj, CorrectionAudit):
                obj.audit_id = uuid.uuid4()
                obj.corrected_at = datetime.now(tz=timezone.utc)
                captured_audits.append(obj)

        db.add = MagicMock(side_effect=capture_add)

        async def mock_refresh(obj):
            pass

        db.refresh = AsyncMock(side_effect=mock_refresh)

        # First execute: load lab_result; second: load member for ownership check
        db.execute = AsyncMock(
            side_effect=[
                _db_result(lab),
                _db_result(member),
            ]
        )

        body = FieldCorrectionRequest(field_name="test_name", new_value="Blood Glucose")

        response = await patch_entity_field(
            entity_type="lab_result",
            entity_id=lab.result_id,
            body=body,
            current_user=user,
            db=db,
        )

        # Entity field was updated
        assert lab.test_name == "Blood Glucose"
        # Audit record was created and committed
        assert len(captured_audits) == 1
        assert captured_audits[0].field_name == "test_name"
        assert captured_audits[0].new_value == "Blood Glucose"
        db.commit.assert_called_once()

        # Response contains correct data
        assert response.entity_type == "lab_result"
        assert response.field_name == "test_name"
        assert response.new_value == "Blood Glucose"

    @pytest.mark.asyncio
    async def test_patch_unknown_entity_type_returns_400(self):
        """Passing an unknown entity_type raises HTTP 400."""
        user = _make_user()
        db = _mock_db()

        body = FieldCorrectionRequest(field_name="drug_name", new_value="Aspirin")

        with pytest.raises(HTTPException) as exc_info:
            await patch_entity_field(
                entity_type="unicorn",
                entity_id=uuid.uuid4(),
                body=body,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 400
        assert "INVALID_ENTITY_TYPE" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_patch_unknown_field_returns_400(self):
        """Passing a field_name not in ALLOWED_FIELDS for the entity_type raises HTTP 400."""
        user = _make_user()
        db = _mock_db()

        body = FieldCorrectionRequest(field_name="secret_internal_field", new_value="whatever")

        with pytest.raises(HTTPException) as exc_info:
            await patch_entity_field(
                entity_type="lab_result",
                entity_id=uuid.uuid4(),
                body=body,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 400
        assert "INVALID_FIELD" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_patch_wrong_user_returns_403(self):
        """Patching an entity owned by another user raises HTTP 403."""
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)  # owned by someone else
        lab = _make_lab_result(member_id=member.member_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[
                _db_result(lab),
                _db_result(member),
            ]
        )

        body = FieldCorrectionRequest(field_name="test_name", new_value="Changed")

        with pytest.raises(HTTPException) as exc_info:
            await patch_entity_field(
                entity_type="lab_result",
                entity_id=lab.result_id,
                body=body,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403
        assert "ACCESS_DENIED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_patch_entity_not_found_returns_404(self):
        """Patching a non-existent entity raises HTTP 404."""
        user = _make_user()
        db = _mock_db()

        db.execute = AsyncMock(return_value=_db_result(None))

        body = FieldCorrectionRequest(field_name="test_name", new_value="New Value")

        with pytest.raises(HTTPException) as exc_info:
            await patch_entity_field(
                entity_type="lab_result",
                entity_id=uuid.uuid4(),
                body=body,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404
        assert "ENTITY_NOT_FOUND" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# Tests: GET /corrections/{entity_type}/{entity_id}
# ---------------------------------------------------------------------------


class TestGetCorrectionHistory:
    @pytest.mark.asyncio
    async def test_get_correction_history_returns_list(self):
        """GET correction history returns a list of CorrectionAuditResponse items."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        lab = _make_lab_result(member_id=member.member_id)
        audit1 = _make_audit(entity_type="lab_result", entity_id=lab.result_id)
        audit2 = _make_audit(entity_type="lab_result", entity_id=lab.result_id)
        db = _mock_db()

        # execute calls: load entity, load member for ownership, load audit records
        db.execute = AsyncMock(
            side_effect=[
                _db_result(lab),
                _db_result(member),
                _db_scalars_result([audit1, audit2]),
            ]
        )

        response = await get_correction_history(
            entity_type="lab_result",
            entity_id=lab.result_id,
            current_user=user,
            db=db,
        )

        assert isinstance(response, list)
        assert len(response) == 2
        assert response[0].entity_type == "lab_result"
        assert response[0].field_name == "test_name"
