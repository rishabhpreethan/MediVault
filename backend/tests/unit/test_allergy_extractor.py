"""Unit tests for app.nlp.allergy_extractor — MV-044."""
from __future__ import annotations

import logging
import sys
import uuid
from types import ModuleType
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Inject fake 'spacy' and 'boto3' so tests work without those packages locally.
# ---------------------------------------------------------------------------
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

if "boto3" not in sys.modules:
    _fake_boto3 = ModuleType("boto3")
    sys.modules["boto3"] = _fake_boto3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_extractor(raw_text: str = "", member_id: uuid.UUID | None = None):
    from app.nlp.allergy_extractor import AllergyExtractor  # noqa: PLC0415
    return AllergyExtractor(member_id=member_id or uuid.uuid4(), raw_text=raw_text)


# ---------------------------------------------------------------------------
# Pattern matching — minimum required tests
# ---------------------------------------------------------------------------

class TestAllergyPatternMatching:
    def test_allergic_to_pattern_matched(self):
        text = "Patient is allergic to Penicillin."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Penicillin" in results[0].allergen_name

    def test_allergy_colon_pattern_matched(self):
        text = "Allergy: Sulfa drugs"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Sulfa drugs" in results[0].allergen_name

    def test_nkda_creates_nkda_record(self):
        text = "NKDA"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].allergen_name == "NKDA"
        assert results[0].reaction_type == "none"

    def test_no_match_returns_empty_list(self):
        text = "Patient presents with fever and cough. Blood pressure is normal."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_confidence_is_low(self):
        text = "allergic to Aspirin"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].confidence_score == "LOW"

    def test_truncates_long_allergen_name(self):
        long_name = "A" * 300
        text = f"allergic to {long_name}"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert len(results[0].allergen_name) <= 255

    def test_no_known_drug_allergies_creates_nkda_record(self):
        text = "No known drug allergies reported."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].allergen_name == "NKDA"

    def test_hypersensitivity_pattern_matched(self):
        text = "Patient has hypersensitivity to aspirin."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "aspirin" in results[0].allergen_name.lower()

    def test_known_allergy_to_pattern_matched(self):
        text = "known allergy to sulfonamides"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "sulfonamides" in results[0].allergen_name

    def test_empty_text_returns_empty_list(self):
        extractor = _make_extractor(raw_text="")
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_multiple_allergies_extracted(self):
        text = "allergic to Penicillin\nallergic to Latex"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 2


# ---------------------------------------------------------------------------
# ORM field assignment
# ---------------------------------------------------------------------------

class TestAllergyOrmFields:
    def test_document_id_set(self):
        text = "allergic to Aspirin"
        doc_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set(self):
        text = "allergic to Aspirin"
        member_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text, member_id=member_id)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].member_id == member_id

    def test_is_manual_entry_false(self):
        text = "allergic to Penicillin"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].is_manual_entry is False

    def test_non_nkda_reaction_type_is_none(self):
        text = "allergic to Codeine"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].reaction_type is None


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestAllergyPhiNotLogged:
    def test_allergen_name_not_in_logs(self, caplog):
        secret_allergen = "TopSecretAllergen_PHI_XYZ_9999"
        text = f"allergic to {secret_allergen}"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.allergy_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert secret_allergen not in record.getMessage()
            assert secret_allergen not in str(record.__dict__)

    def test_count_is_logged(self, caplog):
        text = "allergic to Aspirin"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.INFO, logger="app.nlp.allergy_extractor"):
            extractor.extract([], uuid.uuid4())
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "allergies_found" in all_log_text or "AllergyExtractor" in all_log_text
