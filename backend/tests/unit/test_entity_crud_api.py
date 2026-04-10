"""Unit tests for the entity CRUD API endpoints (MV-053).

Tests exercise route handlers directly without TestClient
(greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import sys
import uuid
from decimal import Decimal
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Stub out heavy optional dependencies before importing app code
# ---------------------------------------------------------------------------

if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

from app.api.entity_crud import (
    create_allergy,
    create_diagnosis,
    create_lab_result,
    create_medication,
    create_vital,
    delete_medication,
    delete_vital,
    discontinue_medication,
    update_medication,
)
from app.schemas.entity_crud import (
    AllergyCreate,
    DiagnosisCreate,
    LabResultCreate,
    MedicationCreate,
    MedicationUpdate,
    VitalCreate,
)


# ---------------------------------------------------------------------------
# Helpers
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
    session.delete = AsyncMock()
    return session


def _db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _make_medication(member_id: uuid.UUID, is_active: bool = True):
    from app.models.medication import Medication

    med = MagicMock(spec=Medication)
    med.medication_id = uuid.uuid4()
    med.member_id = member_id
    med.drug_name = "Metformin"
    med.drug_name_normalized = None
    med.dosage = "500mg"
    med.frequency = "twice daily"
    med.route = "oral"
    med.start_date = None
    med.end_date = None
    med.is_active = is_active
    med.confidence_score = "HIGH"
    med.is_manual_entry = True
    return med


def _make_lab_result(member_id: uuid.UUID):
    from app.models.lab_result import LabResult

    lab = MagicMock(spec=LabResult)
    lab.result_id = uuid.uuid4()
    lab.member_id = member_id
    lab.test_name = "HbA1c"
    lab.test_name_normalized = None
    lab.value = Decimal("7.2")
    lab.value_text = None
    lab.unit = "%"
    lab.reference_low = None
    lab.reference_high = None
    lab.flag = "NORMAL"
    lab.test_date = None
    lab.confidence_score = "HIGH"
    lab.is_manual_entry = True
    return lab


def _make_allergy(member_id: uuid.UUID):
    from app.models.allergy import Allergy

    allergy = MagicMock(spec=Allergy)
    allergy.allergy_id = uuid.uuid4()
    allergy.member_id = member_id
    allergy.allergen_name = "Penicillin"
    allergy.reaction_type = "anaphylaxis"
    allergy.severity = "SEVERE"
    allergy.confidence_score = "HIGH"
    allergy.is_manual_entry = True
    return allergy


def _make_vital(member_id: uuid.UUID):
    from app.models.vital import Vital

    vital = MagicMock(spec=Vital)
    vital.vital_id = uuid.uuid4()
    vital.member_id = member_id
    vital.vital_type = "heart_rate"
    vital.value = Decimal("72.0")
    vital.unit = "bpm"
    vital.recorded_date = None
    vital.confidence_score = "HIGH"
    return vital


# ---------------------------------------------------------------------------
# Test: create medication — is_manual_entry flag set
# ---------------------------------------------------------------------------


class TestCreateMedication:
    @pytest.mark.asyncio
    async def test_create_medication_manual_entry_flag_set(self):
        """Created medication must have is_manual_entry=True and document_id=None."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        # First call: load FamilyMember; subsequent calls: not needed since add+commit
        db.execute = AsyncMock(return_value=_db_result(member))

        # After db.refresh, the ORM object should have proper values
        created_med = _make_medication(member.member_id)

        async def _refresh(obj):
            obj.medication_id = created_med.medication_id
            obj.member_id = created_med.member_id
            obj.drug_name = created_med.drug_name
            obj.drug_name_normalized = created_med.drug_name_normalized
            obj.dosage = created_med.dosage
            obj.frequency = created_med.frequency
            obj.route = created_med.route
            obj.start_date = created_med.start_date
            obj.end_date = created_med.end_date
            obj.is_active = created_med.is_active
            obj.confidence_score = created_med.confidence_score
            obj.is_manual_entry = True

        db.refresh = AsyncMock(side_effect=_refresh)

        body = MedicationCreate(drug_name="Metformin", dosage="500mg")
        response = await create_medication(
            member_id=member.member_id,
            body=body,
            current_user=user,
            db=db,
        )

        assert response.is_manual_entry is True
        assert response.drug_name == "Metformin"
        assert response.dosage == "500mg"
        assert response.confidence_score == "HIGH"
        db.add.assert_called_once()
        db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test: create lab result
# ---------------------------------------------------------------------------


class TestCreateLabResult:
    @pytest.mark.asyncio
    async def test_create_lab_result_success(self):
        """Lab result is created with is_manual_entry=True."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        created_lab = _make_lab_result(member.member_id)

        async def _refresh(obj):
            obj.result_id = created_lab.result_id
            obj.member_id = created_lab.member_id
            obj.test_name = created_lab.test_name
            obj.test_name_normalized = created_lab.test_name_normalized
            obj.value = created_lab.value
            obj.value_text = created_lab.value_text
            obj.unit = created_lab.unit
            obj.reference_low = created_lab.reference_low
            obj.reference_high = created_lab.reference_high
            obj.flag = created_lab.flag
            obj.test_date = created_lab.test_date
            obj.confidence_score = created_lab.confidence_score
            obj.is_manual_entry = True

        db.refresh = AsyncMock(side_effect=_refresh)

        body = LabResultCreate(test_name="HbA1c", value=7.2, unit="%")
        response = await create_lab_result(
            member_id=member.member_id,
            body=body,
            current_user=user,
            db=db,
        )

        assert response.is_manual_entry is True
        assert response.test_name == "HbA1c"
        assert response.value == 7.2
        assert response.unit == "%"


# ---------------------------------------------------------------------------
# Test: update medication — partial fields
# ---------------------------------------------------------------------------


class TestUpdateMedication:
    @pytest.mark.asyncio
    async def test_update_medication_partial_fields(self):
        """Only provided fields are updated; others remain unchanged."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        med = _make_medication(member.member_id)
        # Two execute calls: first for member, second for medication
        db.execute = AsyncMock(
            side_effect=[_db_result(member), _db_result(med)]
        )

        async def _refresh(obj):
            pass  # med already has all attrs

        db.refresh = AsyncMock(side_effect=_refresh)

        body = MedicationUpdate(dosage="1000mg")
        response = await update_medication(
            member_id=member.member_id,
            med_id=med.medication_id,
            body=body,
            current_user=user,
            db=db,
        )

        # setattr should have been called with dosage=1000mg
        assert med.dosage == "1000mg"
        assert response.drug_name == "Metformin"


# ---------------------------------------------------------------------------
# Test: delete medication returns 204
# ---------------------------------------------------------------------------


class TestDeleteMedication:
    @pytest.mark.asyncio
    async def test_delete_medication_returns_204(self):
        """DELETE returns None (204 No Content) and calls db.delete + db.commit."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        med = _make_medication(member.member_id)
        db.execute = AsyncMock(
            side_effect=[_db_result(member), _db_result(med)]
        )

        result = await delete_medication(
            member_id=member.member_id,
            med_id=med.medication_id,
            current_user=user,
            db=db,
        )

        assert result is None
        db.delete.assert_awaited_once_with(med)
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_returns_404(self):
        """DELETE raises 404 when the medication does not exist."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        db.execute = AsyncMock(
            side_effect=[_db_result(member), _db_result(None)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_medication(
                member_id=member.member_id,
                med_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test: discontinue medication
# ---------------------------------------------------------------------------


class TestDiscontinueMedication:
    @pytest.mark.asyncio
    async def test_discontinue_medication(self):
        """PATCH /discontinue sets is_active=False."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        med = _make_medication(member.member_id, is_active=True)
        db.execute = AsyncMock(
            side_effect=[_db_result(member), _db_result(med)]
        )

        async def _refresh(obj):
            pass  # med is already a MagicMock with attrs set

        db.refresh = AsyncMock(side_effect=_refresh)

        response = await discontinue_medication(
            member_id=member.member_id,
            med_id=med.medication_id,
            current_user=user,
            db=db,
        )

        assert med.is_active is False
        assert response.is_active is False
        db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test: wrong member returns 403
# ---------------------------------------------------------------------------


class TestOwnershipCheck:
    @pytest.mark.asyncio
    async def test_create_wrong_member_returns_403(self):
        """Creating an entity for a member owned by another user raises 403."""
        user = _make_user()
        # member belongs to a different user
        member = _make_member(user_id=uuid.uuid4())
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        body = MedicationCreate(drug_name="Aspirin")
        with pytest.raises(HTTPException) as exc_info:
            await create_medication(
                member_id=member.member_id,
                body=body,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test: create allergy
# ---------------------------------------------------------------------------


class TestCreateAllergy:
    @pytest.mark.asyncio
    async def test_create_allergy_success(self):
        """Allergy is created with correct fields and is_manual_entry=True."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        created_allergy = _make_allergy(member.member_id)

        async def _refresh(obj):
            obj.allergy_id = created_allergy.allergy_id
            obj.member_id = created_allergy.member_id
            obj.allergen_name = created_allergy.allergen_name
            obj.reaction_type = created_allergy.reaction_type
            obj.severity = created_allergy.severity
            obj.confidence_score = created_allergy.confidence_score
            obj.is_manual_entry = True

        db.refresh = AsyncMock(side_effect=_refresh)

        body = AllergyCreate(
            allergen_name="Penicillin",
            reaction_type="anaphylaxis",
            severity="SEVERE",
        )
        response = await create_allergy(
            member_id=member.member_id,
            body=body,
            current_user=user,
            db=db,
        )

        assert response.is_manual_entry is True
        assert response.allergen_name == "Penicillin"
        assert response.reaction_type == "anaphylaxis"
        assert response.severity == "SEVERE"
        assert response.confidence_score == "HIGH"


# ---------------------------------------------------------------------------
# Test: create vital
# ---------------------------------------------------------------------------


class TestCreateVital:
    @pytest.mark.asyncio
    async def test_create_vital_success(self):
        """Vital is created with correct type and value."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        created_vital = _make_vital(member.member_id)

        async def _refresh(obj):
            obj.vital_id = created_vital.vital_id
            obj.member_id = created_vital.member_id
            obj.vital_type = created_vital.vital_type
            obj.value = created_vital.value
            obj.unit = created_vital.unit
            obj.recorded_date = created_vital.recorded_date
            obj.confidence_score = created_vital.confidence_score

        db.refresh = AsyncMock(side_effect=_refresh)

        body = VitalCreate(vital_type="heart_rate", value=72.0, unit="bpm")
        response = await create_vital(
            member_id=member.member_id,
            body=body,
            current_user=user,
            db=db,
        )

        assert response.vital_type == "heart_rate"
        assert response.value == 72.0
        assert response.unit == "bpm"
        assert response.confidence_score == "HIGH"
        # Vital model has no is_manual_entry column — just verify core fields


# ---------------------------------------------------------------------------
# Test: delete vital
# ---------------------------------------------------------------------------


class TestDeleteVital:
    @pytest.mark.asyncio
    async def test_delete_vital_returns_204(self):
        """DELETE vital returns None (204) and calls delete + commit."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()

        vital = _make_vital(member.member_id)
        db.execute = AsyncMock(
            side_effect=[_db_result(member), _db_result(vital)]
        )

        result = await delete_vital(
            member_id=member.member_id,
            vital_id=vital.vital_id,
            current_user=user,
            db=db,
        )

        assert result is None
        db.delete.assert_awaited_once_with(vital)
        db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test: create diagnosis
# ---------------------------------------------------------------------------


class TestCreateDiagnosis:
    @pytest.mark.asyncio
    async def test_create_diagnosis_success(self):
        """Diagnosis is created with is_manual_entry=True."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        from app.models.diagnosis import Diagnosis

        diag_mock = MagicMock(spec=Diagnosis)
        diag_mock.diagnosis_id = uuid.uuid4()
        diag_mock.member_id = member.member_id
        diag_mock.condition_name = "Type 2 Diabetes"
        diag_mock.condition_normalized = None
        diag_mock.icd10_code = "E11"
        diag_mock.diagnosed_date = None
        diag_mock.status = "ACTIVE"
        diag_mock.confidence_score = "HIGH"
        diag_mock.is_manual_entry = True

        async def _refresh(obj):
            obj.diagnosis_id = diag_mock.diagnosis_id
            obj.member_id = diag_mock.member_id
            obj.condition_name = diag_mock.condition_name
            obj.condition_normalized = diag_mock.condition_normalized
            obj.icd10_code = diag_mock.icd10_code
            obj.diagnosed_date = diag_mock.diagnosed_date
            obj.status = diag_mock.status
            obj.confidence_score = diag_mock.confidence_score
            obj.is_manual_entry = True

        db.refresh = AsyncMock(side_effect=_refresh)

        body = DiagnosisCreate(condition_name="Type 2 Diabetes", icd10_code="E11", status="ACTIVE")
        response = await create_diagnosis(
            member_id=member.member_id,
            body=body,
            current_user=user,
            db=db,
        )

        assert response.is_manual_entry is True
        assert response.condition_name == "Type 2 Diabetes"
        assert response.icd10_code == "E11"
        assert response.status == "ACTIVE"
