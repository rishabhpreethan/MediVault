"""Unit tests for app.nlp.diagnosis_extractor — MV-043."""
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

def _make_extractor(raw_text: str = "", member_id: uuid.UUID | None = None):
    from app.nlp.diagnosis_extractor import DiagnosisExtractor  # noqa: PLC0415
    return DiagnosisExtractor(member_id=member_id or uuid.uuid4(), raw_text=raw_text)


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

class TestDiagnosisPatternMatching:
    def test_diagnosed_with_phrase_matched(self):
        text = "Patient was diagnosed with Type 2 Diabetes Mellitus."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Type 2 Diabetes Mellitus" in results[0].condition_name

    def test_impression_colon_matched(self):
        text = "Impression: Bilateral pneumonia"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Bilateral pneumonia" in results[0].condition_name

    def test_assessment_colon_matched(self):
        text = "Assessment: Hypertension, uncontrolled"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Hypertension" in results[0].condition_name

    def test_diagnosis_colon_matched(self):
        text = "Diagnosis: Iron deficiency anemia"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert "Iron deficiency anemia" in results[0].condition_name

    def test_case_insensitive_matching(self):
        text = "DIAGNOSED WITH Chronic kidney disease"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1

    def test_impression_with_colon_matched(self):
        text = "Impression: Acute myocardial infarction"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1

    def test_multiple_triggers_in_text(self):
        text = (
            "Diagnosis: Hypertension\n"
            "Assessment: Dyslipidemia\n"
            "Patient was diagnosed with Obesity"
        )
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 3

    def test_empty_text_returns_empty_list(self):
        extractor = _make_extractor(raw_text="")
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_text_without_trigger_phrases_returns_empty(self):
        text = "Patient presents with fever. Temperature is 38.5 degrees."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_condition_stops_at_period(self):
        text = "Diagnosis: Asthma. Patient advised to use inhaler."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        # Condition should not include text after the period
        assert "Patient advised" not in results[0].condition_name

    def test_condition_stops_at_newline(self):
        text = "Assessment: COPD\nPatient is a smoker."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert "Patient is a smoker" not in results[0].condition_name

    def test_entities_argument_ignored(self):
        """DiagnosisExtractor ignores the entities list — uses raw_text only."""
        text = "Diagnosis: Gout"
        extractor = _make_extractor(raw_text=text)
        fake_entities = [{"text": "Aspirin", "label": "DRUG", "start": 0, "end": 7}]
        results = extractor.extract(fake_entities, uuid.uuid4())
        assert len(results) == 1
        assert "Gout" in results[0].condition_name


# ---------------------------------------------------------------------------
# ORM field assignment
# ---------------------------------------------------------------------------

class TestDiagnosisOrmFields:
    def test_document_id_set(self):
        text = "Diagnosis: Gout"
        doc_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set(self):
        text = "Diagnosis: Gout"
        member_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text, member_id=member_id)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].member_id == member_id

    def test_is_manual_entry_false(self):
        text = "Diagnosis: Gout"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].is_manual_entry is False

    def test_status_defaults_to_unknown(self):
        text = "Diagnosis: Gout"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].status == "UNKNOWN"


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

class TestDiagnosisConfidence:
    def test_all_results_low_confidence(self):
        text = (
            "Diagnosis: Hypertension\n"
            "Assessment: Dyslipidemia\n"
            "diagnosed with Obesity"
        )
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert all(r.confidence_score == "LOW" for r in results)

    def test_single_result_low_confidence(self):
        text = "Impression: Atrial fibrillation"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].confidence_score == "LOW"


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestDiagnosisPhiNotLogged:
    def test_condition_name_not_in_logs(self, caplog):
        secret_condition = "TopSecretCondition_PHI_XYZ_9999"
        text = f"Diagnosis: {secret_condition}"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.diagnosis_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert secret_condition not in record.getMessage()
            assert secret_condition not in str(record.__dict__)

    def test_count_is_logged(self, caplog):
        text = "Diagnosis: Hypertension"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.INFO, logger="app.nlp.diagnosis_extractor"):
            extractor.extract([], uuid.uuid4())
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "diagnoses_found" in all_log_text or "DiagnosisExtractor" in all_log_text
