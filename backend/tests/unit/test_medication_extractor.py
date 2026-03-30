"""Unit tests for app.nlp.medication_extractor — MV-041."""
from __future__ import annotations

import logging
import sys
import uuid
from types import ModuleType
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Inject a fake 'spacy' module so tests work without spaCy installed locally.
# ---------------------------------------------------------------------------
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ent(text: str, label: str, start: int) -> dict:
    return {"text": text, "label": label, "start": start, "end": start + len(text)}


def _make_extractor(member_id: uuid.UUID | None = None):
    """Return a MedicationExtractor with a fresh member_id."""
    from app.nlp.medication_extractor import MedicationExtractor  # noqa: PLC0415
    return MedicationExtractor(member_id=member_id or uuid.uuid4())


# ---------------------------------------------------------------------------
# Grouping logic
# ---------------------------------------------------------------------------

class TestMedicationGrouping:
    def test_single_drug_no_attributes_returns_one_medication(self):
        extractor = _make_extractor()
        entities = [_ent("Aspirin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert len(results) == 1

    def test_drug_name_set_on_orm_instance(self):
        extractor = _make_extractor()
        entities = [_ent("Metformin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].drug_name == "Metformin"

    def test_nearby_dosage_is_linked(self):
        # DRUG at 0, DOSAGE at 10 — within 200-char window
        extractor = _make_extractor()
        entities = [
            _ent("Aspirin", "DRUG", 0),
            _ent("100mg", "DOSAGE", 10),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].dosage == "100mg"

    def test_nearby_frequency_is_linked(self):
        extractor = _make_extractor()
        entities = [
            _ent("Lisinopril", "DRUG", 0),
            _ent("once daily", "FREQUENCY", 12),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].frequency == "once daily"

    def test_nearby_route_is_linked(self):
        extractor = _make_extractor()
        entities = [
            _ent("Morphine", "DRUG", 0),
            _ent("oral", "ROUTE", 10),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].route == "oral"

    def test_out_of_window_dosage_is_not_linked(self):
        # DOSAGE placed 300 chars away — outside the ±200 window
        extractor = _make_extractor()
        drug_start = 0
        dosage_start = 300
        entities = [
            _ent("Aspirin", "DRUG", drug_start),
            _ent("500mg", "DOSAGE", dosage_start),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        # Dosage is too far — should NOT be linked
        assert results[0].dosage is None

    def test_multiple_drugs_each_get_their_own_instance(self):
        extractor = _make_extractor()
        entities = [
            _ent("Aspirin", "DRUG", 0),
            _ent("Metformin", "DRUG", 50),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert len(results) == 2
        drug_names = {r.drug_name for r in results}
        assert drug_names == {"Aspirin", "Metformin"}

    def test_document_id_set_on_orm_instance(self):
        extractor = _make_extractor()
        doc_id = uuid.uuid4()
        entities = [_ent("Ibuprofen", "DRUG", 0)]
        results = extractor.extract(entities, doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set_on_orm_instance(self):
        member_id = uuid.uuid4()
        extractor = _make_extractor(member_id=member_id)
        entities = [_ent("Paracetamol", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].member_id == member_id

    def test_is_manual_entry_false(self):
        extractor = _make_extractor()
        entities = [_ent("Atorvastatin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].is_manual_entry is False

    def test_empty_entities_returns_empty_list(self):
        extractor = _make_extractor()
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_only_dosage_entities_no_drug_returns_empty(self):
        extractor = _make_extractor()
        entities = [_ent("100mg", "DOSAGE", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results == []


# ---------------------------------------------------------------------------
# Confidence levels
# ---------------------------------------------------------------------------

class TestConfidenceLevels:
    def test_high_confidence_when_drug_and_dosage_present(self):
        extractor = _make_extractor()
        entities = [
            _ent("Warfarin", "DRUG", 0),
            _ent("5mg", "DOSAGE", 10),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].confidence_score == "HIGH"

    def test_medium_confidence_when_drug_only(self):
        extractor = _make_extractor()
        entities = [_ent("Warfarin", "DRUG", 0)]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].confidence_score == "MEDIUM"

    def test_medium_confidence_drug_with_frequency_but_no_dosage(self):
        extractor = _make_extractor()
        entities = [
            _ent("Amoxicillin", "DRUG", 0),
            _ent("twice daily", "FREQUENCY", 15),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        # Dosage absent — confidence stays MEDIUM
        assert results[0].confidence_score == "MEDIUM"

    def test_high_confidence_drug_with_dosage_and_frequency(self):
        extractor = _make_extractor()
        entities = [
            _ent("Metoprolol", "DRUG", 0),
            _ent("25mg", "DOSAGE", 12),
            _ent("once daily", "FREQUENCY", 18),
        ]
        results = extractor.extract(entities, uuid.uuid4())
        assert results[0].confidence_score == "HIGH"


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestPhiNotLogged:
    def test_drug_name_not_in_logs(self, caplog):
        secret_drug = "TopSecretDrug_PHI_XYZ"
        extractor = _make_extractor()
        entities = [_ent(secret_drug, "DRUG", 0)]
        with caplog.at_level(logging.DEBUG, logger="app.nlp.medication_extractor"):
            extractor.extract(entities, uuid.uuid4())
        for record in caplog.records:
            assert secret_drug not in record.getMessage()
            assert secret_drug not in str(record.__dict__)

    def test_dosage_not_in_logs(self, caplog):
        secret_dosage = "999mgSuperSecret"
        extractor = _make_extractor()
        entities = [
            _ent("SomeDrug", "DRUG", 0),
            _ent(secret_dosage, "DOSAGE", 10),
        ]
        with caplog.at_level(logging.DEBUG, logger="app.nlp.medication_extractor"):
            extractor.extract(entities, uuid.uuid4())
        for record in caplog.records:
            assert secret_dosage not in record.getMessage()
            assert secret_dosage not in str(record.__dict__)

    def test_counts_are_logged(self, caplog):
        extractor = _make_extractor()
        entities = [_ent("DrugA", "DRUG", 0)]
        with caplog.at_level(logging.INFO, logger="app.nlp.medication_extractor"):
            extractor.extract(entities, uuid.uuid4())
        # At least one log record should mention "medications_found" or a count
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "medications_found" in all_log_text or "MedicationExtractor" in all_log_text
