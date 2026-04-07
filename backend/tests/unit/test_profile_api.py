"""Unit tests for the profile API endpoints (MV-051).

Tests exercise the route handlers directly without using TestClient
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

# Inject fake spacy so profile_service can be imported without the real package.
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

from app.api.profile import _load_member_or_404, get_profile, get_profile_summary
from app.services.profile_service import (
    DiagnosisRM,
    HealthProfileRM,
    LabResultRM,
    MedicationRM,
)


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


def _make_health_profile_rm(member_id: uuid.UUID) -> HealthProfileRM:
    """Return a HealthProfileRM with 1 medication, 1 lab result, 1 diagnosis."""
    doc_id = str(uuid.uuid4())
    return HealthProfileRM(
        member_id=str(member_id),
        medications=[
            MedicationRM(
                medication_id=str(uuid.uuid4()),
                drug_name="Metformin",
                dosage="500mg",
                frequency="twice daily",
                route="oral",
                confidence="HIGH",
                is_active=True,
                source_document_id=doc_id,
            )
        ],
        lab_results=[
            LabResultRM(
                lab_result_id=str(uuid.uuid4()),
                test_name="HbA1c",
                value="7.2",
                unit="%",
                confidence="HIGH",
                recorded_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
                source_document_id=doc_id,
            )
        ],
        diagnoses=[
            DiagnosisRM(
                diagnosis_id=str(uuid.uuid4()),
                condition_name="Type 2 Diabetes",
                status="active",
                confidence="HIGH",
                source_document_id=doc_id,
            )
        ],
        generated_at=datetime.now(tz=timezone.utc),
    )


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
    async def test_raises_403_when_wrong_user(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())  # different user
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await _load_member_or_404(db, member.member_id, user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: get_profile
# ---------------------------------------------------------------------------


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_get_profile_returns_health_profile(self):
        """Mock get_health_profile to return a HealthProfileRM and verify response shape."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        profile_rm = _make_health_profile_rm(member.member_id)

        with patch(
            "app.api.profile.profile_service.get_health_profile",
            new_callable=AsyncMock,
            return_value=profile_rm,
        ):
            response = await get_profile(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert response.member_id == str(member.member_id)
        assert len(response.medications) == 1
        assert len(response.lab_results) == 1
        assert len(response.diagnoses) == 1

        med = response.medications[0]
        assert med.drug_name == "Metformin"
        assert med.dosage == "500mg"
        assert med.confidence_score == "HIGH"
        assert med.is_active is True

        lab = response.lab_results[0]
        assert lab.test_name == "HbA1c"
        assert lab.value == "7.2"
        assert lab.unit == "%"

        diag = response.diagnoses[0]
        assert diag.condition_name == "Type 2 Diabetes"
        assert diag.status == "active"

    @pytest.mark.asyncio
    async def test_get_profile_raises_404_when_member_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await get_profile(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_profile_raises_403_when_wrong_user(self):
        user = _make_user()
        member = _make_member(user_id=uuid.uuid4())  # different user
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_profile(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: get_profile_summary
# ---------------------------------------------------------------------------


class TestGetProfileSummary:
    @pytest.mark.asyncio
    async def test_get_summary_returns_counts(self):
        """Mock get_profile_summary to return a dict with counts and verify response."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        summary_dict = {
            "medication_count": 3,
            "lab_result_count": 7,
            "diagnosis_count": 2,
            "low_confidence_count": 1,
        }

        with patch(
            "app.api.profile.profile_service.get_profile_summary",
            new_callable=AsyncMock,
            return_value=summary_dict,
        ):
            response = await get_profile_summary(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert response.member_id == str(member.member_id)
        assert response.total_medications == 3
        assert response.total_lab_results == 7
        assert response.total_diagnoses == 2
        assert response.low_confidence_count == 1

    @pytest.mark.asyncio
    async def test_get_summary_member_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await get_profile_summary(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404
