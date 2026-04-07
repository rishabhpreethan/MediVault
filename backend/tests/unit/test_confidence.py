"""Unit tests for app.nlp.confidence — MV-047."""
from __future__ import annotations

import pytest

from app.nlp.confidence import (
    ConfidenceLevel,
    flag_low_confidence,
    score_diagnosis,
    score_lab,
    score_medication,
)


# ---------------------------------------------------------------------------
# score_medication
# ---------------------------------------------------------------------------

class TestScoreMedication:
    def test_high_when_drug_and_dosage(self):
        assert score_medication(drug_found=True, dosage_found=True, frequency_found=False) == ConfidenceLevel.HIGH

    def test_high_when_drug_dosage_and_frequency(self):
        assert score_medication(drug_found=True, dosage_found=True, frequency_found=True) == ConfidenceLevel.HIGH

    def test_medium_when_drug_only(self):
        assert score_medication(drug_found=True, dosage_found=False, frequency_found=False) == ConfidenceLevel.MEDIUM

    def test_medium_when_drug_and_frequency_but_no_dosage(self):
        # Frequency alone does not elevate to HIGH
        assert score_medication(drug_found=True, dosage_found=False, frequency_found=True) == ConfidenceLevel.MEDIUM

    def test_low_when_no_drug(self):
        assert score_medication(drug_found=False, dosage_found=False, frequency_found=False) == ConfidenceLevel.LOW

    def test_low_when_no_drug_but_dosage_present(self):
        # Dosage without a drug entity is still LOW
        assert score_medication(drug_found=False, dosage_found=True, frequency_found=False) == ConfidenceLevel.LOW

    def test_low_when_no_drug_but_frequency_present(self):
        assert score_medication(drug_found=False, dosage_found=False, frequency_found=True) == ConfidenceLevel.LOW

    def test_returns_confidence_level_enum(self):
        result = score_medication(drug_found=True, dosage_found=True, frequency_found=False)
        assert isinstance(result, ConfidenceLevel)


# ---------------------------------------------------------------------------
# score_lab
# ---------------------------------------------------------------------------

class TestScoreLab:
    def test_high_when_value_and_unit(self):
        assert score_lab(value_found=True, unit_found=True) == ConfidenceLevel.HIGH

    def test_medium_when_value_only(self):
        assert score_lab(value_found=True, unit_found=False) == ConfidenceLevel.MEDIUM

    def test_low_when_no_value(self):
        assert score_lab(value_found=False, unit_found=False) == ConfidenceLevel.LOW

    def test_low_when_unit_only(self):
        # Unit without a value is LOW (no numeric result)
        assert score_lab(value_found=False, unit_found=True) == ConfidenceLevel.LOW

    def test_returns_confidence_level_enum(self):
        result = score_lab(value_found=True, unit_found=True)
        assert isinstance(result, ConfidenceLevel)


# ---------------------------------------------------------------------------
# score_diagnosis
# ---------------------------------------------------------------------------

class TestScoreDiagnosis:
    def test_medium_for_diagnosed_with(self):
        assert score_diagnosis("diagnosed with") == ConfidenceLevel.MEDIUM

    def test_medium_for_diagnosed_with_mixed_case(self):
        assert score_diagnosis("Diagnosed With") == ConfidenceLevel.MEDIUM

    def test_medium_for_diagnosed_with_extra_whitespace(self):
        assert score_diagnosis("  diagnosed with  ") == ConfidenceLevel.MEDIUM

    def test_low_for_impression(self):
        assert score_diagnosis("impression") == ConfidenceLevel.LOW

    def test_low_for_assessment(self):
        assert score_diagnosis("assessment") == ConfidenceLevel.LOW

    def test_low_for_diagnosis(self):
        assert score_diagnosis("diagnosis") == ConfidenceLevel.LOW

    def test_low_for_unknown_trigger(self):
        assert score_diagnosis("history of") == ConfidenceLevel.LOW

    def test_low_for_empty_string(self):
        assert score_diagnosis("") == ConfidenceLevel.LOW

    def test_returns_confidence_level_enum(self):
        result = score_diagnosis("diagnosed with")
        assert isinstance(result, ConfidenceLevel)


# ---------------------------------------------------------------------------
# flag_low_confidence
# ---------------------------------------------------------------------------

class TestFlagLowConfidence:
    # ----- helper objects -----

    class _FakeItem:
        """Minimal object with a confidence_score attribute."""

        def __init__(self, confidence: str) -> None:
            self.confidence_score = confidence

    def test_low_item_needs_review(self):
        item = self._FakeItem("LOW")
        result = flag_low_confidence([item])
        assert result[0]["needs_review"] is True

    def test_medium_item_no_review(self):
        item = self._FakeItem("MEDIUM")
        result = flag_low_confidence([item])
        assert result[0]["needs_review"] is False

    def test_high_item_no_review(self):
        item = self._FakeItem("HIGH")
        result = flag_low_confidence([item])
        assert result[0]["needs_review"] is False

    def test_mixed_list_flags_only_low(self):
        items = [
            self._FakeItem("HIGH"),
            self._FakeItem("MEDIUM"),
            self._FakeItem("LOW"),
            self._FakeItem("LOW"),
        ]
        results = flag_low_confidence(items)
        needs_review_flags = [r["needs_review"] for r in results]
        assert needs_review_flags == [False, False, True, True]

    def test_empty_list_returns_empty(self):
        assert flag_low_confidence([]) == []

    def test_item_preserved_in_output(self):
        item = self._FakeItem("LOW")
        result = flag_low_confidence([item])
        assert result[0]["item"] is item

    def test_dict_items_supported(self):
        items = [
            {"confidence_score": "LOW"},
            {"confidence_score": "HIGH"},
        ]
        results = flag_low_confidence(items)
        assert results[0]["needs_review"] is True
        assert results[1]["needs_review"] is False

    def test_custom_confidence_field(self):
        class _Custom:
            def __init__(self, val: str) -> None:
                self.my_conf = val

        items = [_Custom("LOW"), _Custom("MEDIUM")]
        results = flag_low_confidence(items, confidence_field="my_conf")
        assert results[0]["needs_review"] is True
        assert results[1]["needs_review"] is False

    def test_missing_field_defaults_to_no_review(self):
        """Item without the confidence field should not raise; needs_review=False."""

        class _NoConf:
            pass

        results = flag_low_confidence([_NoConf()])
        assert results[0]["needs_review"] is False

    def test_confidence_level_enum_value_low_flagged(self):
        """Accept ConfidenceLevel.LOW enum as value (not just raw string)."""
        item = self._FakeItem(ConfidenceLevel.LOW)  # type: ignore[arg-type]
        result = flag_low_confidence([item])
        assert result[0]["needs_review"] is True
