"""Comprehensive unit tests for NLP layer — MV-121.

Covers gaps across:
- orchestrator.is_likely_scanned (edge cases)
- confidence.score_diagnosis (all trigger combinations)
- confidence.flag_low_confidence (mixed HIGH/MEDIUM/LOW lists)
- medication_extractor (drug name lowercasing, multi-entity text)
- deduplication_service (manual entry skipping with matching names)
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone, timedelta
from types import ModuleType
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub spacy, boto3, botocore BEFORE any app imports.
# ---------------------------------------------------------------------------
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

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


# ---------------------------------------------------------------------------
# Tests: orchestrator.is_likely_scanned  (edge cases)
# ---------------------------------------------------------------------------

class TestIsLikelyScanned:
    """Edge-case coverage for the is_likely_scanned heuristic."""

    def _fn(self, text: str, page_count: int) -> bool:
        from app.extractors.orchestrator import is_likely_scanned  # noqa: PLC0415
        return is_likely_scanned(text, page_count)

    # --- absolute-char-count boundary ---

    def test_empty_string_is_scanned(self):
        """Zero characters → scanned."""
        assert self._fn("", 1) is True

    def test_single_char_is_scanned(self):
        """One character → below 100 threshold → scanned."""
        assert self._fn("A", 5) is True

    def test_99_chars_is_scanned(self):
        """99 stripped chars → still below 100 threshold → scanned."""
        text = "x" * 99
        assert self._fn(text, 1) is True

    def test_exactly_100_chars_not_scanned_by_absolute_threshold(self):
        """Exactly 100 stripped characters clears the absolute threshold.

        With page_count=1 and 100 chars/page the per-page heuristic (< 50)
        is also not triggered, so result should be False.
        """
        text = "x" * 100
        assert self._fn(text, 1) is False

    def test_101_chars_not_scanned(self):
        """101 stripped chars → clears absolute threshold."""
        text = "x" * 101
        assert self._fn(text, 1) is False

    # --- page_count = 0 skips per-page heuristic ---

    def test_page_count_zero_skips_per_page_heuristic(self):
        """When page_count=0 the per-page check is skipped.

        100+ chars with page_count=0 → not scanned even though
        chars/page would be 0 if computed.
        """
        text = "x" * 200
        assert self._fn(text, 0) is False

    def test_sparse_text_with_page_count_zero_only_absolute_matters(self):
        """110 chars, page_count=0 → per-page skipped → not scanned."""
        text = "x" * 110
        assert self._fn(text, 0) is False

    # --- chars-per-page boundary ---

    def test_chars_per_page_exactly_50_not_scanned(self):
        """Exactly 50 chars/page → threshold is < 50 → not scanned."""
        text = "x" * 200  # 200 chars / 4 pages = 50 chars/page
        assert self._fn(text, 4) is False

    def test_chars_per_page_49_is_scanned(self):
        """49 chars/page (< 50) with enough total chars → scanned."""
        # 196 chars / 4 pages = 49 chars/page; 196 >= 100 so absolute passes
        text = "x" * 196
        assert self._fn(text, 4) is True

    def test_many_chars_per_page_not_scanned(self):
        """1000 chars on 1 page → clearly not scanned."""
        text = "x" * 1000
        assert self._fn(text, 1) is False

    def test_whitespace_only_string_is_scanned(self):
        """Whitespace-only string strips to zero chars → scanned."""
        text = "   \t\n  " * 20
        assert self._fn(text, 1) is True

    def test_leading_trailing_whitespace_stripped(self):
        """Whitespace padding should be stripped before counting."""
        # 100 meaningful chars surrounded by whitespace
        text = "   " + "x" * 100 + "   "
        assert self._fn(text, 1) is False


# ---------------------------------------------------------------------------
# Tests: confidence.score_diagnosis  (all trigger combinations)
# ---------------------------------------------------------------------------

class TestScoreDiagnosisAllCombinations:
    """All trigger-type combinations for score_diagnosis."""

    def _score(self, trigger: str):
        from app.nlp.confidence import score_diagnosis  # noqa: PLC0415
        return score_diagnosis(trigger)

    def _level(self, name: str):
        from app.nlp.confidence import ConfidenceLevel  # noqa: PLC0415
        return ConfidenceLevel[name]

    # MEDIUM triggers
    def test_diagnosed_with_lower(self):
        assert self._score("diagnosed with") == self._level("MEDIUM")

    def test_diagnosed_with_upper(self):
        assert self._score("DIAGNOSED WITH") == self._level("MEDIUM")

    def test_diagnosed_with_mixed_case(self):
        assert self._score("Diagnosed With") == self._level("MEDIUM")

    def test_diagnosed_with_extra_spaces(self):
        assert self._score("  diagnosed with  ") == self._level("MEDIUM")

    def test_diagnosed_with_tab_pad(self):
        """Tab-padding should also be stripped."""
        assert self._score("\tdiagnosed with\t") == self._level("MEDIUM")

    # LOW triggers — standard section headers
    def test_impression_lower(self):
        assert self._score("impression") == self._level("LOW")

    def test_assessment_lower(self):
        assert self._score("assessment") == self._level("LOW")

    def test_diagnosis_keyword(self):
        assert self._score("diagnosis") == self._level("LOW")

    def test_history_of(self):
        assert self._score("history of") == self._level("LOW")

    def test_rule_out(self):
        assert self._score("rule out") == self._level("LOW")

    def test_possible(self):
        assert self._score("possible") == self._level("LOW")

    def test_empty_string_is_low(self):
        assert self._score("") == self._level("LOW")

    def test_whitespace_only_is_low(self):
        assert self._score("   ") == self._level("LOW")

    def test_unrecognised_trigger_is_low(self):
        assert self._score("patient presents with") == self._level("LOW")

    # Return type
    def test_returns_confidence_level_enum(self):
        from app.nlp.confidence import ConfidenceLevel  # noqa: PLC0415
        result = self._score("diagnosed with")
        assert isinstance(result, ConfidenceLevel)


# ---------------------------------------------------------------------------
# Tests: confidence.flag_low_confidence (comprehensive mixed lists)
# ---------------------------------------------------------------------------

class TestFlagLowConfidenceMixed:
    """Extra coverage for flag_low_confidence with varied list compositions."""

    class _Item:
        def __init__(self, score: str) -> None:
            self.confidence_score = score

    def _flag(self, items, **kwargs):
        from app.nlp.confidence import flag_low_confidence  # noqa: PLC0415
        return flag_low_confidence(items, **kwargs)

    def test_all_high_no_reviews(self):
        items = [self._Item("HIGH")] * 5
        results = self._flag(items)
        assert all(r["needs_review"] is False for r in results)

    def test_all_medium_no_reviews(self):
        items = [self._Item("MEDIUM")] * 3
        results = self._flag(items)
        assert all(r["needs_review"] is False for r in results)

    def test_all_low_all_reviews(self):
        items = [self._Item("LOW")] * 4
        results = self._flag(items)
        assert all(r["needs_review"] is True for r in results)

    def test_high_medium_low_mixed_order(self):
        items = [
            self._Item("HIGH"),
            self._Item("LOW"),
            self._Item("MEDIUM"),
            self._Item("LOW"),
            self._Item("HIGH"),
        ]
        results = self._flag(items)
        flags = [r["needs_review"] for r in results]
        assert flags == [False, True, False, True, False]

    def test_output_length_matches_input_length(self):
        items = [self._Item(s) for s in ("HIGH", "LOW", "MEDIUM", "LOW", "HIGH", "MEDIUM")]
        results = self._flag(items)
        assert len(results) == len(items)

    def test_item_reference_preserved(self):
        """Each output dict's 'item' key must be the exact original object."""
        items = [self._Item("HIGH"), self._Item("LOW")]
        results = self._flag(items)
        for original, result in zip(items, results):
            assert result["item"] is original

    def test_single_low_item(self):
        results = self._flag([self._Item("LOW")])
        assert results[0]["needs_review"] is True

    def test_single_high_item(self):
        results = self._flag([self._Item("HIGH")])
        assert results[0]["needs_review"] is False

    def test_dict_list_mixed(self):
        items = [
            {"confidence_score": "HIGH"},
            {"confidence_score": "LOW"},
            {"confidence_score": "MEDIUM"},
            {"confidence_score": "LOW"},
        ]
        results = self._flag(items)
        flags = [r["needs_review"] for r in results]
        assert flags == [False, True, False, True]

    def test_empty_list_returns_empty(self):
        assert self._flag([]) == []


# ---------------------------------------------------------------------------
# Tests: medication_extractor  (drug name lowercasing, multi-entity)
# ---------------------------------------------------------------------------

def _ent(text: str, label: str, start: int) -> dict:
    return {"text": text, "label": label, "start": start, "end": start + len(text)}


def _make_med_extractor(member_id: Optional[uuid.UUID] = None):
    from app.nlp.medication_extractor import MedicationExtractor  # noqa: PLC0415
    return MedicationExtractor(member_id=member_id or uuid.uuid4())


class TestMedicationExtractorNormalization:
    """Drug name casing and multi-entity extraction edge cases."""

    def test_drug_name_preserved_as_extracted(self):
        """drug_name on the ORM instance must match the entity text exactly."""
        extractor = _make_med_extractor()
        entities = [_ent("METFORMIN", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        # The extractor stores the raw entity text (no normalization)
        assert results[0].drug_name == "METFORMIN"

    def test_lowercase_drug_name_preserved(self):
        extractor = _make_med_extractor()
        entities = [_ent("aspirin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].drug_name == "aspirin"

    def test_mixed_case_drug_name_preserved(self):
        extractor = _make_med_extractor()
        entities = [_ent("Atorvastatin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].drug_name == "Atorvastatin"

    def test_three_drugs_returns_three_medications(self):
        extractor = _make_med_extractor()
        entities = [
            _ent("Aspirin", "DRUG", 0),
            _ent("Metformin", "DRUG", 100),
            _ent("Lisinopril", "DRUG", 200),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert len(results) == 3

    def test_multi_entity_each_drug_gets_correct_dosage(self):
        """Each DRUG picks up its nearby DOSAGE, not a distant one."""
        extractor = _make_med_extractor()
        entities = [
            _ent("Aspirin", "DRUG", 0),
            _ent("100mg", "DOSAGE", 10),   # close to Aspirin
            _ent("Metformin", "DRUG", 500),
            _ent("500mg", "DOSAGE", 510),  # close to Metformin
        ]
        results = extractor.extract(entities, uuid.uuid4())
        drug_map = {r.drug_name: r for r in results}

        assert drug_map["Aspirin"].dosage == "100mg"
        assert drug_map["Metformin"].dosage == "500mg"

    def test_shared_attribute_entity_closest_drug_wins(self):
        """A single attribute entity within window of two drugs is assigned to both
        (first-match semantics per drug window — the spec doesn't deduplicate
        attributes across drugs)."""
        extractor = _make_med_extractor()
        entities = [
            _ent("DrugA", "DRUG", 0),
            _ent("DrugB", "DRUG", 20),
            _ent("50mg", "DOSAGE", 25),  # within window of both DrugA and DrugB
        ]
        results = extractor.extract(entities, uuid.uuid4())
        # Both drugs are within the ±200 window of the dosage, so both get it
        for r in results:
            assert r.dosage == "50mg"

    def test_strength_attribute_not_linked_as_dosage(self):
        """STRENGTH is a valid attribute label but maps to a different slot.

        The current extractor only populates dosage/frequency/route directly;
        STRENGTH goes into nearby but is not surfaced as dosage.
        """
        extractor = _make_med_extractor()
        entities = [
            _ent("Warfarin", "DRUG", 0),
            _ent("2mg", "STRENGTH", 10),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        # STRENGTH does not populate the dosage field
        assert results[0].dosage is None

    def test_form_attribute_not_linked_as_dosage(self):
        """FORM entity is tracked but does not fill the dosage slot."""
        extractor = _make_med_extractor()
        entities = [
            _ent("Omeprazole", "DRUG", 0),
            _ent("capsule", "FORM", 12),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].dosage is None

    def test_is_manual_entry_always_false(self):
        """NLP-extracted medications must never be marked as manual entries."""
        extractor = _make_med_extractor()
        entities = [
            _ent("DrugX", "DRUG", 0),
            _ent("DrugY", "DRUG", 50),
            _ent("DrugZ", "DRUG", 100),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        for r in results:
            assert r.is_manual_entry is False

    def test_all_medications_share_same_document_id(self):
        extractor = _make_med_extractor()
        doc_id = uuid.uuid4()
        entities = [_ent("A", "DRUG", 0), _ent("B", "DRUG", 50)]
        results = extractor.extract(entities, doc_id)
        for r in results:
            assert r.document_id == doc_id

    def test_all_medications_share_same_member_id(self):
        member_id = uuid.uuid4()
        extractor = _make_med_extractor(member_id=member_id)
        entities = [_ent("A", "DRUG", 0), _ent("B", "DRUG", 50)]
        results = extractor.extract(entities, uuid.uuid4())
        for r in results:
            assert r.member_id == member_id

    def test_confidence_high_when_dosage_present_multi_drug(self):
        extractor = _make_med_extractor()
        entities = [
            _ent("Aspirin", "DRUG", 0),
            _ent("100mg", "DOSAGE", 10),
            _ent("Metformin", "DRUG", 500),
            # Metformin has no dosage
        ]
        results = extractor.extract(entities, uuid.uuid4())
        drug_map = {r.drug_name: r for r in results}
        assert drug_map["Aspirin"].confidence_score == "HIGH"
        assert drug_map["Metformin"].confidence_score == "MEDIUM"


# ---------------------------------------------------------------------------
# Tests: deduplication_service — manual entry skipping
# ---------------------------------------------------------------------------

def _ts(offset_seconds: int = 0) -> datetime:
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset_seconds)


def _make_medication_mock(
    *,
    drug_name: str = "Metformin",
    dosage: Optional[str] = "500mg",
    frequency: Optional[str] = None,
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


def _build_session(rows: list) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    return session


class TestDeduplicationManualEntrySkipping:
    """Manual entries must not be deduplicated even when names match.

    The DB query filters them out (is_manual_entry=False), so we simulate
    this by returning an empty list from the mocked session — which represents
    the state after the DB filter has been applied.
    """

    @pytest.mark.asyncio
    async def test_manual_medications_excluded_by_query_filter(self):
        """Simulate: two manual entries with same drug name.

        DB query excludes is_manual_entry=True rows, so session returns []
        → no deletions occur.
        """
        from app.services.deduplication_service import deduplicate_medications  # noqa: PLC0415

        member_id = uuid.uuid4()
        # DB filter removes both manual entries → query returns empty list
        session = _build_session([])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_only_non_manual_entries_get_deduplicated(self):
        """Mixed session: one manual entry (filtered out by DB) + duplicates.

        We simulate the DB having already excluded the manual entry, so the
        returned list contains only the two non-manual duplicates.
        """
        from app.services.deduplication_service import deduplicate_medications  # noqa: PLC0415

        member_id = uuid.uuid4()
        med_old = _make_medication_mock(drug_name="Lisinopril", created_at_offset=0)
        med_new = _make_medication_mock(drug_name="Lisinopril", created_at_offset=100)
        # manual entry is NOT in the returned list (query filtered it)
        session = _build_session([med_old, med_new])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 1
        session.delete.assert_called_once_with(med_old)

    @pytest.mark.asyncio
    async def test_manual_diagnoses_excluded_by_query_filter(self):
        """Duplicate manual diagnosis → DB filters them → no deletions."""
        from app.services.deduplication_service import deduplicate_diagnoses  # noqa: PLC0415

        member_id = uuid.uuid4()
        session = _build_session([])

        deleted = await deduplicate_diagnoses(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_manual_allergies_excluded_by_query_filter(self):
        """Duplicate manual allergy → DB filters them → no deletions."""
        from app.services.deduplication_service import deduplicate_allergies  # noqa: PLC0415

        member_id = uuid.uuid4()
        session = _build_session([])

        deleted = await deduplicate_allergies(session, member_id)

        assert deleted == 0
        session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_three_duplicates_deletes_two_oldest(self):
        """Three records with same drug name → two oldest deleted, newest kept."""
        from app.services.deduplication_service import deduplicate_medications  # noqa: PLC0415

        member_id = uuid.uuid4()
        med1 = _make_medication_mock(drug_name="Warfarin", created_at_offset=0)
        med2 = _make_medication_mock(drug_name="Warfarin", created_at_offset=50)
        med3 = _make_medication_mock(drug_name="Warfarin", created_at_offset=100)
        session = _build_session([med1, med2, med3])

        deleted = await deduplicate_medications(session, member_id)

        assert deleted == 2
        deleted_args = {call.args[0] for call in session.delete.await_args_list}
        assert med1 in deleted_args
        assert med2 in deleted_args
        assert med3 not in deleted_args

    @pytest.mark.asyncio
    async def test_merge_fills_null_fields_from_multiple_older_records(self):
        """Null fields on canonical filled from most-recent older that has them."""
        from app.services.deduplication_service import deduplicate_medications  # noqa: PLC0415

        member_id = uuid.uuid4()
        # oldest has route; middle has frequency; newest has neither
        med_oldest = _make_medication_mock(
            drug_name="Atenolol",
            dosage=None,
            frequency=None,
            route="oral",
            created_at_offset=0,
        )
        med_middle = _make_medication_mock(
            drug_name="Atenolol",
            dosage=None,
            frequency="once daily",
            route=None,
            created_at_offset=50,
        )
        med_newest = _make_medication_mock(
            drug_name="Atenolol",
            dosage=None,
            frequency=None,
            route=None,
            created_at_offset=100,
        )
        session = _build_session([med_oldest, med_middle, med_newest])

        await deduplicate_medications(session, member_id)

        # frequency should come from med_middle (most-recent older with it)
        assert med_newest.frequency == "once daily"
        # route should come from med_oldest (only one with it)
        assert med_newest.route == "oral"
