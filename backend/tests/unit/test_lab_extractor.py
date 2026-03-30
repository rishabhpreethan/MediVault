"""Unit tests for app.nlp.lab_extractor — MV-042."""
from __future__ import annotations

import logging
import sys
import uuid
from decimal import Decimal
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
    from app.nlp.lab_extractor import LabExtractor  # noqa: PLC0415
    return LabExtractor(member_id=member_id or uuid.uuid4(), raw_text=raw_text)


# ---------------------------------------------------------------------------
# Regex parsing
# ---------------------------------------------------------------------------

class TestLabRegexParsing:
    def test_simple_integer_value_parsed(self):
        text = "WBC: 8200 /uL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].test_name == "WBC"
        assert results[0].value == Decimal("8200")
        assert results[0].unit == "/uL"

    def test_decimal_value_parsed(self):
        text = "Hemoglobin: 13.5 g/dL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].test_name == "Hemoglobin"
        assert results[0].value == Decimal("13.5")
        assert results[0].unit == "g/dL"

    def test_value_without_unit_parsed(self):
        text = "pH: 7.4"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].value == Decimal("7.4")
        assert results[0].unit is None

    def test_multiword_test_name_parsed(self):
        text = "Blood Glucose: 95 mg/dL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].test_name == "Blood Glucose"

    def test_multiple_results_from_multiline_text(self):
        text = "Hemoglobin: 13.5 g/dL\nWBC: 8200 /uL\nPlatelets: 250000 /uL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 3

    def test_empty_text_returns_empty_list(self):
        extractor = _make_extractor(raw_text="")
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_text_with_no_lab_patterns_returns_empty(self):
        text = "Patient presents with fever and chills."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_percentage_unit_parsed(self):
        text = "Hematocrit: 42 %"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) == 1
        assert results[0].unit == "%"

    def test_value_text_set_on_instance(self):
        text = "Creatinine: 1.2 mg/dL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].value_text == "1.2"


# ---------------------------------------------------------------------------
# ORM field assignment
# ---------------------------------------------------------------------------

class TestLabOrmFields:
    def test_document_id_set(self):
        text = "WBC: 5000 /uL"
        doc_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set(self):
        text = "WBC: 5000 /uL"
        member_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text, member_id=member_id)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].member_id == member_id

    def test_is_manual_entry_false(self):
        text = "WBC: 5000 /uL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].is_manual_entry is False

    def test_entities_argument_ignored(self):
        """LabExtractor ignores the entities list — uses raw_text only."""
        text = "Sodium: 140 mEq/L"
        extractor = _make_extractor(raw_text=text)
        fake_entities = [
            {"text": "Aspirin", "label": "DRUG", "start": 0, "end": 7}
        ]
        results = extractor.extract(fake_entities, uuid.uuid4())
        # Should still produce one lab result from raw text, ignoring DRUG entity
        assert len(results) == 1
        assert results[0].test_name == "Sodium"


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

class TestLabConfidence:
    def test_all_results_medium_confidence(self):
        text = "WBC: 8200 /uL\nHemoglobin: 13.5 g/dL"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert all(r.confidence_score == "MEDIUM" for r in results)


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestLabPhiNotLogged:
    def test_test_name_not_in_logs(self, caplog):
        secret_test = "SuperSecretTestName_PHI_999"
        text = f"{secret_test}: 42 mg/dL"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.lab_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert secret_test not in record.getMessage()
            assert secret_test not in str(record.__dict__)

    def test_value_not_in_logs(self, caplog):
        # Use a distinctive numeric string unlikely to appear in log metadata
        text = "Glucose: 99999.1234 mg/dL"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.lab_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert "99999.1234" not in record.getMessage()
            assert "99999.1234" not in str(record.__dict__)

    def test_count_is_logged(self, caplog):
        text = "WBC: 8200 /uL"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.INFO, logger="app.nlp.lab_extractor"):
            extractor.extract([], uuid.uuid4())
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "labs_found" in all_log_text or "LabExtractor" in all_log_text
