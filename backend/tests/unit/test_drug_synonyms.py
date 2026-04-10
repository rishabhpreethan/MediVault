"""MV-049: Unit tests for drug synonym normalization."""
from __future__ import annotations

import pytest

from app.nlp.drug_synonyms import normalize_drug_name, DRUG_SYNONYMS


class TestNormalizeDrugName:
    """Tests for normalize_drug_name()."""

    def test_known_synonym_paracetamol(self):
        """'paracetamol' should map to canonical 'Acetaminophen'."""
        assert normalize_drug_name("paracetamol") == "Acetaminophen"

    def test_known_synonym_crocin(self):
        """Indian brand 'crocin' should map to 'Acetaminophen'."""
        assert normalize_drug_name("crocin") == "Acetaminophen"

    def test_known_synonym_brufen(self):
        """Indian brand 'brufen' should map to 'Ibuprofen'."""
        assert normalize_drug_name("brufen") == "Ibuprofen"

    def test_already_canonical_ibuprofen(self):
        """'ibuprofen' has no mapping — should be returned as-is."""
        assert normalize_drug_name("ibuprofen") == "ibuprofen"

    def test_already_canonical_metformin(self):
        """'metformin' has no mapping — should be returned unchanged."""
        assert normalize_drug_name("metformin") == "metformin"

    def test_unknown_drug_preserves_casing(self):
        """Unknown drug name should be returned with its original casing."""
        assert normalize_drug_name("Warfarin") == "Warfarin"

    def test_case_insensitive_matching_upper(self):
        """PARACETAMOL (all-caps) should still match and return 'Acetaminophen'."""
        assert normalize_drug_name("PARACETAMOL") == "Acetaminophen"

    def test_case_insensitive_matching_mixed(self):
        """Mixed-case brand name should still resolve to canonical form."""
        assert normalize_drug_name("Crocin") == "Acetaminophen"

    def test_empty_string(self):
        """Empty string should be returned as empty string."""
        assert normalize_drug_name("") == ""

    def test_whitespace_trimming(self):
        """Leading/trailing whitespace should be stripped before lookup."""
        assert normalize_drug_name("  paracetamol  ") == "Acetaminophen"

    def test_whitespace_only_string(self):
        """Whitespace-only input has no mapping — returned as-is (original)."""
        result = normalize_drug_name("   ")
        # No synonym for blank key; original input is returned unchanged
        assert result == "   "

    def test_global_brand_lipitor(self):
        """Global brand 'lipitor' should map to 'Atorvastatin'."""
        assert normalize_drug_name("lipitor") == "Atorvastatin"

    def test_global_brand_zithromax(self):
        """Global brand 'zithromax' should map to 'Azithromycin'."""
        assert normalize_drug_name("zithromax") == "Azithromycin"

    def test_drug_synonyms_dict_nonempty(self):
        """DRUG_SYNONYMS dictionary must contain at least 10 entries."""
        assert len(DRUG_SYNONYMS) >= 10

    def test_all_dict_values_are_title_cased(self):
        """Every canonical name in the dictionary must be title-cased."""
        for synonym, canonical in DRUG_SYNONYMS.items():
            assert canonical == canonical.title(), (
                f"Canonical for '{synonym}' is '{canonical}', expected title-cased"
            )
