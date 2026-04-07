"""Unit tests for app.services.profile_service — MV-050.

All DB interactions are mocked — no real database required.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.profile_service import (
    DiagnosisRM,
    HealthProfileRM,
    LabResultRM,
    MedicationRM,
    get_health_profile,
    get_profile_summary,
)


# ---------------------------------------------------------------------------
# Factories for fake ORM instances
# ---------------------------------------------------------------------------

def _make_medication(
    *,
    member_id: Optional[uuid.UUID] = None,
    drug_name: str = "TestDrug",
    dosage: Optional[str] = "10mg",
    frequency: Optional[str] = "once daily",
    route: Optional[str] = "oral",
    confidence_score: str = "HIGH",
    is_active: bool = True,
    document_id: Optional[uuid.UUID] = None,
) -> MagicMock:
    m = MagicMock()
    m.medication_id = uuid.uuid4()
    m.member_id = member_id or uuid.uuid4()
    m.drug_name = drug_name
    m.dosage = dosage
    m.frequency = frequency
    m.route = route
    m.confidence_score = confidence_score
    m.is_active = is_active
    m.document_id = document_id
    return m


def _make_lab_result(
    *,
    member_id: Optional[uuid.UUID] = None,
    test_name: str = "Hemoglobin",
    value: Optional[Decimal] = Decimal("13.5"),
    value_text: Optional[str] = None,
    unit: Optional[str] = "g/dL",
    confidence_score: str = "HIGH",
    test_date: Optional[date] = None,
    document_id: Optional[uuid.UUID] = None,
) -> MagicMock:
    lr = MagicMock()
    lr.result_id = uuid.uuid4()
    lr.member_id = member_id or uuid.uuid4()
    lr.test_name = test_name
    lr.value = value
    lr.value_text = value_text
    lr.unit = unit
    lr.confidence_score = confidence_score
    lr.test_date = test_date
    lr.document_id = document_id
    return lr


def _make_diagnosis(
    *,
    member_id: Optional[uuid.UUID] = None,
    condition_name: str = "Hypertension",
    status: str = "ACTIVE",
    confidence_score: str = "LOW",
    document_id: Optional[uuid.UUID] = None,
) -> MagicMock:
    d = MagicMock()
    d.diagnosis_id = uuid.uuid4()
    d.member_id = member_id or uuid.uuid4()
    d.condition_name = condition_name
    d.status = status
    d.confidence_score = confidence_score
    d.document_id = document_id
    return d


# ---------------------------------------------------------------------------
# Mock AsyncSession helper
# ---------------------------------------------------------------------------

def _build_mock_session(
    medications: list,
    lab_results: list,
    diagnoses: list,
) -> AsyncMock:
    """Return a mock AsyncSession whose execute() returns rows for each table query.

    Calls are expected in order: medications → lab_results → diagnoses.
    """
    session = AsyncMock()

    def _scalar_result(rows: list) -> MagicMock:
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    # execute() is called three times; return a different result each time
    session.execute.side_effect = [
        _scalar_result(medications),
        _scalar_result(lab_results),
        _scalar_result(diagnoses),
    ]
    return session


# ---------------------------------------------------------------------------
# get_health_profile
# ---------------------------------------------------------------------------

class TestGetHealthProfile:
    @pytest.mark.asyncio
    async def test_returns_health_profile_rm(self):
        session = _build_mock_session([], [], [])
        member_id = uuid.uuid4()
        result = await get_health_profile(session, member_id)
        assert isinstance(result, HealthProfileRM)

    @pytest.mark.asyncio
    async def test_member_id_on_profile(self):
        member_id = uuid.uuid4()
        session = _build_mock_session([], [], [])
        result = await get_health_profile(session, member_id)
        assert result.member_id == str(member_id)

    @pytest.mark.asyncio
    async def test_medications_mapped_to_medication_rm(self):
        med = _make_medication(confidence_score="HIGH")
        session = _build_mock_session([med], [], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert len(result.medications) == 1
        assert isinstance(result.medications[0], MedicationRM)

    @pytest.mark.asyncio
    async def test_medication_fields_mapped_correctly(self):
        doc_id = uuid.uuid4()
        med = _make_medication(
            drug_name="Metformin",
            dosage="500mg",
            frequency="twice daily",
            route="oral",
            confidence_score="HIGH",
            is_active=True,
            document_id=doc_id,
        )
        session = _build_mock_session([med], [], [])
        result = await get_health_profile(session, uuid.uuid4())
        rm = result.medications[0]
        assert rm.drug_name == "Metformin"
        assert rm.dosage == "500mg"
        assert rm.frequency == "twice daily"
        assert rm.route == "oral"
        assert rm.confidence == "HIGH"
        assert rm.is_active is True
        assert rm.source_document_id == str(doc_id)

    @pytest.mark.asyncio
    async def test_medication_source_document_id_none_when_no_doc(self):
        med = _make_medication(document_id=None)
        session = _build_mock_session([med], [], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.medications[0].source_document_id is None

    @pytest.mark.asyncio
    async def test_lab_results_mapped_to_lab_result_rm(self):
        lr = _make_lab_result(confidence_score="HIGH")
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert len(result.lab_results) == 1
        assert isinstance(result.lab_results[0], LabResultRM)

    @pytest.mark.asyncio
    async def test_lab_result_value_as_string(self):
        lr = _make_lab_result(value=Decimal("13.5"), value_text=None)
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.lab_results[0].value == "13.5"

    @pytest.mark.asyncio
    async def test_lab_result_prefers_value_text(self):
        lr = _make_lab_result(value=Decimal("13.5"), value_text="13.5 (estimated)")
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.lab_results[0].value == "13.5 (estimated)"

    @pytest.mark.asyncio
    async def test_lab_result_value_none_when_both_absent(self):
        lr = _make_lab_result(value=None, value_text=None)
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.lab_results[0].value is None

    @pytest.mark.asyncio
    async def test_lab_result_recorded_at_from_test_date(self):
        lr = _make_lab_result(test_date=date(2025, 6, 15))
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        rm = result.lab_results[0]
        assert rm.recorded_at is not None
        assert rm.recorded_at.year == 2025
        assert rm.recorded_at.month == 6
        assert rm.recorded_at.day == 15

    @pytest.mark.asyncio
    async def test_lab_result_recorded_at_none_when_no_test_date(self):
        lr = _make_lab_result(test_date=None)
        session = _build_mock_session([], [lr], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.lab_results[0].recorded_at is None

    @pytest.mark.asyncio
    async def test_diagnoses_mapped_to_diagnosis_rm(self):
        diag = _make_diagnosis(confidence_score="LOW")
        session = _build_mock_session([], [], [diag])
        result = await get_health_profile(session, uuid.uuid4())
        assert len(result.diagnoses) == 1
        assert isinstance(result.diagnoses[0], DiagnosisRM)

    @pytest.mark.asyncio
    async def test_diagnosis_fields_mapped_correctly(self):
        doc_id = uuid.uuid4()
        diag = _make_diagnosis(
            condition_name="Type 2 Diabetes",
            status="ACTIVE",
            confidence_score="MEDIUM",
            document_id=doc_id,
        )
        session = _build_mock_session([], [], [diag])
        result = await get_health_profile(session, uuid.uuid4())
        rm = result.diagnoses[0]
        assert rm.condition_name == "Type 2 Diabetes"
        assert rm.status == "ACTIVE"
        assert rm.confidence == "MEDIUM"
        assert rm.source_document_id == str(doc_id)

    @pytest.mark.asyncio
    async def test_generated_at_is_datetime(self):
        session = _build_mock_session([], [], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert isinstance(result.generated_at, datetime)

    @pytest.mark.asyncio
    async def test_empty_member_returns_empty_lists(self):
        """An unknown member_id returns a valid HealthProfileRM with empty lists."""
        session = _build_mock_session([], [], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert result.medications == []
        assert result.lab_results == []
        assert result.diagnoses == []

    @pytest.mark.asyncio
    async def test_multiple_medications_all_returned(self):
        meds = [_make_medication(drug_name=f"Drug{i}") for i in range(3)]
        session = _build_mock_session(meds, [], [])
        result = await get_health_profile(session, uuid.uuid4())
        assert len(result.medications) == 3

    @pytest.mark.asyncio
    async def test_multiple_lab_results_all_returned(self):
        labs = [_make_lab_result(test_name=f"Test{i}") for i in range(4)]
        session = _build_mock_session([], labs, [])
        result = await get_health_profile(session, uuid.uuid4())
        assert len(result.lab_results) == 4


# ---------------------------------------------------------------------------
# get_profile_summary
# ---------------------------------------------------------------------------

class TestGetProfileSummary:
    @pytest.mark.asyncio
    async def test_summary_counts_correctly(self):
        meds = [_make_medication(confidence_score="HIGH"), _make_medication(confidence_score="MEDIUM")]
        labs = [_make_lab_result(confidence_score="LOW")]
        diags = [_make_diagnosis(confidence_score="LOW"), _make_diagnosis(confidence_score="MEDIUM")]
        session = _build_mock_session(meds, labs, diags)
        summary = await get_profile_summary(session, uuid.uuid4())

        assert summary["medication_count"] == 2
        assert summary["lab_result_count"] == 1
        assert summary["diagnosis_count"] == 2

    @pytest.mark.asyncio
    async def test_low_confidence_count_correct(self):
        meds = [
            _make_medication(confidence_score="HIGH"),
            _make_medication(confidence_score="LOW"),
        ]
        labs = [
            _make_lab_result(confidence_score="LOW"),
            _make_lab_result(confidence_score="MEDIUM"),
        ]
        diags = [_make_diagnosis(confidence_score="LOW")]
        session = _build_mock_session(meds, labs, diags)
        summary = await get_profile_summary(session, uuid.uuid4())
        # 1 LOW med + 1 LOW lab + 1 LOW diag = 3
        assert summary["low_confidence_count"] == 3

    @pytest.mark.asyncio
    async def test_no_low_confidence_items(self):
        meds = [_make_medication(confidence_score="HIGH")]
        labs = [_make_lab_result(confidence_score="HIGH")]
        diags = [_make_diagnosis(confidence_score="MEDIUM")]
        session = _build_mock_session(meds, labs, diags)
        summary = await get_profile_summary(session, uuid.uuid4())
        assert summary["low_confidence_count"] == 0

    @pytest.mark.asyncio
    async def test_empty_member_all_counts_zero(self):
        """Empty member returns all counts as zero without raising."""
        session = _build_mock_session([], [], [])
        summary = await get_profile_summary(session, uuid.uuid4())
        assert summary["medication_count"] == 0
        assert summary["lab_result_count"] == 0
        assert summary["diagnosis_count"] == 0
        assert summary["low_confidence_count"] == 0

    @pytest.mark.asyncio
    async def test_summary_returns_dict(self):
        session = _build_mock_session([], [], [])
        result = await get_profile_summary(session, uuid.uuid4())
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_summary_has_all_required_keys(self):
        session = _build_mock_session([], [], [])
        result = await get_profile_summary(session, uuid.uuid4())
        assert "medication_count" in result
        assert "lab_result_count" in result
        assert "diagnosis_count" in result
        assert "low_confidence_count" in result
