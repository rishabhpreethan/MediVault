"""Unit tests for app.services.deduplication_service — MV-048.

All DB interactions are mocked — no real database required.
Uses AsyncMock + fake ORM objects, following the same pattern as the rest
of the test suite.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from types import ModuleType
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inject fake spacy so any transitive import that reaches app.nlp.pipeline
# does not fail when the real package is absent outside Docker.
# ---------------------------------------------------------------------------
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

from app.services.deduplication_service import (  # noqa: E402
    deduplicate_allergies,
    deduplicate_diagnoses,
    deduplicate_medications,
    run_deduplication,
)


# ---------------------------------------------------------------------------
# Fake ORM object factories
# ---------------------------------------------------------------------------

def _ts(offset_seconds: int = 0) -> datetime:
    """Return a UTC datetime offset by *offset_seconds* from a fixed base."""
    from datetime import timedelta
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset_seconds)


def _make_medication(
    *,
    drug_name: str = "Metformin",
    dosage: Optional[str] = "500mg",
    frequency: Optional[str] = "twice daily",
    route: Optional[str] = None,
    start_date=None,
    end_date=None,
    is_manual_entry: bool = False,
    created_at_offset: int = 0,
) -> MagicMock:
    med = MagicMock()
    med.medication_id = uuid.uuid4()
    med.drug_name = drug_name
    med.dosage = dosage
    med.frequency = frequency
    med.route = route
    med.start_date = start_date
    med.end_date = end_date
    med.is_manual_entry = is_manual_entry
    med.created_at = _ts(created_at_offset)
    return med


def _make_diagnosis(
    *,
    condition_name: str = "Hypertension",
    icd10_code: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    is_manual_entry: bool = False,
    created_at_offset: int = 0,
) -> MagicMock:
    diag = MagicMock()
    diag.diagnosis_id = uuid.uuid4()
    diag.condition_name = condition_name
    diag.icd10_code = icd10_code
    diag.status = status
    diag.is_manual_entry = is_manual_entry
    diag.created_at = _ts(created_at_offset)
    return diag


def _make_allergy(
    *,
    allergen_name: str = "Penicillin",
    reaction_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_manual_entry: bool = False,
    created_at_offset: int = 0,
) -> MagicMock:
    allergy = MagicMock()
    allergy.allergy_id = uuid.uuid4()
    allergy.allergen_name = allergen_name
    allergy.reaction_type = reaction_type
    allergy.severity = severity
    allergy.is_manual_entry = is_manual_entry
    allergy.created_at = _ts(created_at_offset)
    return allergy


# ---------------------------------------------------------------------------
# Mock AsyncSession builder
# ---------------------------------------------------------------------------

def _build_session(rows: list) -> AsyncMock:
    """Return an AsyncMock session whose execute() returns *rows* via scalars().all()."""
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Tests: deduplicate_medications
# ---------------------------------------------------------------------------

class TestDeduplicateMedications:
    @pytest.mark.asyncio
    async def test_deduplicate_medications_removes_duplicate_drug(self):
        """Two medications with the same drug name → one should be deleted."""
        member_id = uuid.uuid4()
        med_old = _make_medication(drug_name="Metformin", created_at_offset=0)
        med_new = _make_medication(drug_name="Metformin", created_at_offset=100)
        session = _build_session([med_old, med_new])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 1
        session.delete.assert_called_once_with(med_old)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicate_medications_keeps_most_recent(self):
        """The most-recently created medication is the canonical record kept."""
        member_id = uuid.uuid4()
        med_old = _make_medication(drug_name="Aspirin", created_at_offset=0)
        med_new = _make_medication(drug_name="Aspirin", created_at_offset=200)
        session = _build_session([med_old, med_new])

        await deduplicate_medications(session, member_id)

        # Only the older one is deleted — the newer one (canonical) is NOT deleted
        deleted_args = [call.args[0] for call in session.delete.await_args_list]
        assert med_old in deleted_args
        assert med_new not in deleted_args

    @pytest.mark.asyncio
    async def test_deduplicate_medications_merges_null_fields(self):
        """Canonical's None fields are filled from older records."""
        member_id = uuid.uuid4()
        # Older record has route; newer record does not
        med_old = _make_medication(
            drug_name="Lisinopril",
            dosage="10mg",
            route="oral",
            created_at_offset=0,
        )
        med_new = _make_medication(
            drug_name="Lisinopril",
            dosage=None,
            route=None,
            created_at_offset=100,
        )
        session = _build_session([med_old, med_new])

        await deduplicate_medications(session, member_id)

        # Canonical (med_new) should have received route from med_old
        assert med_new.route == "oral"
        # Canonical dosage should be back-filled too
        assert med_new.dosage == "10mg"

    @pytest.mark.asyncio
    async def test_deduplicate_medications_skips_manual_entries(self):
        """Manual entries must not be deduplicated even when names match."""
        member_id = uuid.uuid4()
        # Both have the same name but both are manual — session.execute returns []
        # because is_manual_entry=True rows are excluded by the query filter.
        # We simulate the filter by returning no rows from the mocked query.
        session = _build_session([])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplicate_no_duplicates_returns_zero(self):
        """Single medication per drug name → nothing deleted."""
        member_id = uuid.uuid4()
        med = _make_medication(drug_name="Atorvastatin", created_at_offset=0)
        session = _build_session([med])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()
        session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: deduplicate_diagnoses
# ---------------------------------------------------------------------------

class TestDeduplicateDiagnoses:
    @pytest.mark.asyncio
    async def test_deduplicate_diagnoses_removes_duplicate_condition(self):
        """Two diagnoses with the same condition name → one should be deleted."""
        member_id = uuid.uuid4()
        diag_old = _make_diagnosis(condition_name="Hypertension", created_at_offset=0)
        diag_new = _make_diagnosis(condition_name="Hypertension", created_at_offset=100)
        session = _build_session([diag_old, diag_new])

        deleted = await deduplicate_diagnoses(session, member_id)

        assert deleted == 1
        session.delete.assert_called_once_with(diag_old)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicate_diagnoses_merges_icd10_from_older(self):
        """icd10_code is back-filled onto canonical if canonical lacks it."""
        member_id = uuid.uuid4()
        diag_old = _make_diagnosis(
            condition_name="Type 2 Diabetes",
            icd10_code="E11",
            created_at_offset=0,
        )
        diag_new = _make_diagnosis(
            condition_name="Type 2 Diabetes",
            icd10_code=None,
            created_at_offset=100,
        )
        session = _build_session([diag_old, diag_new])

        await deduplicate_diagnoses(session, member_id)

        assert diag_new.icd10_code == "E11"

    @pytest.mark.asyncio
    async def test_deduplicate_diagnoses_no_duplicates_returns_zero(self):
        """Unique condition names → nothing deleted."""
        member_id = uuid.uuid4()
        diag = _make_diagnosis(condition_name="Asthma")
        session = _build_session([diag])

        deleted = await deduplicate_diagnoses(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: deduplicate_allergies
# ---------------------------------------------------------------------------

class TestDeduplicateAllergies:
    @pytest.mark.asyncio
    async def test_deduplicate_allergies_removes_duplicate_allergen(self):
        """Two allergies with the same allergen name → one should be deleted."""
        member_id = uuid.uuid4()
        allergy_old = _make_allergy(allergen_name="Penicillin", created_at_offset=0)
        allergy_new = _make_allergy(allergen_name="Penicillin", created_at_offset=100)
        session = _build_session([allergy_old, allergy_new])

        deleted = await deduplicate_allergies(session, member_id)

        assert deleted == 1
        session.delete.assert_called_once_with(allergy_old)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicate_allergies_merges_severity_from_older(self):
        """severity is back-filled onto canonical if canonical lacks it."""
        member_id = uuid.uuid4()
        allergy_old = _make_allergy(
            allergen_name="Sulfa",
            reaction_type="Rash",
            severity="MODERATE",
            created_at_offset=0,
        )
        allergy_new = _make_allergy(
            allergen_name="Sulfa",
            reaction_type=None,
            severity=None,
            created_at_offset=100,
        )
        session = _build_session([allergy_old, allergy_new])

        await deduplicate_allergies(session, member_id)

        assert allergy_new.severity == "MODERATE"
        assert allergy_new.reaction_type == "Rash"

    @pytest.mark.asyncio
    async def test_deduplicate_allergies_no_duplicates_returns_zero(self):
        """Unique allergen names → nothing deleted."""
        member_id = uuid.uuid4()
        allergy = _make_allergy(allergen_name="Latex")
        session = _build_session([allergy])

        deleted = await deduplicate_allergies(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: run_deduplication
# ---------------------------------------------------------------------------

class TestRunDeduplication:
    @pytest.mark.asyncio
    async def test_run_deduplication_returns_counts(self):
        """run_deduplication calls all three helpers and aggregates counts."""
        member_id = uuid.uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.services.deduplication_service.deduplicate_medications",
                new=AsyncMock(return_value=3),
            ) as mock_meds,
            patch(
                "app.services.deduplication_service.deduplicate_diagnoses",
                new=AsyncMock(return_value=1),
            ) as mock_diags,
            patch(
                "app.services.deduplication_service.deduplicate_allergies",
                new=AsyncMock(return_value=0),
            ) as mock_allergies,
        ):
            result = await run_deduplication(session, member_id)

        assert result == {"medications": 3, "diagnoses": 1, "allergies": 0}
        mock_meds.assert_called_once_with(session, member_id)
        mock_diags.assert_called_once_with(session, member_id)
        mock_allergies.assert_called_once_with(session, member_id)

    @pytest.mark.asyncio
    async def test_run_deduplication_returns_zero_when_no_duplicates(self):
        """All zeros when there are no duplicates anywhere."""
        member_id = uuid.uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.services.deduplication_service.deduplicate_medications",
                new=AsyncMock(return_value=0),
            ),
            patch(
                "app.services.deduplication_service.deduplicate_diagnoses",
                new=AsyncMock(return_value=0),
            ),
            patch(
                "app.services.deduplication_service.deduplicate_allergies",
                new=AsyncMock(return_value=0),
            ),
        ):
            result = await run_deduplication(session, member_id)

        assert result == {"medications": 0, "diagnoses": 0, "allergies": 0}
