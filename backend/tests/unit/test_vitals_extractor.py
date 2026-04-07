"""Unit tests for app.nlp.vitals_extractor — MV-045."""
from __future__ import annotations

import logging
import sys
import uuid
from decimal import Decimal
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
    from app.nlp.vitals_extractor import VitalsExtractor  # noqa: PLC0415
    return VitalsExtractor(member_id=member_id or uuid.uuid4(), raw_text=raw_text)


# ---------------------------------------------------------------------------
# Pattern matching — minimum required tests
# ---------------------------------------------------------------------------

class TestVitalsPatternMatching:
    def test_blood_pressure_extracted(self):
        text = "BP: 120/80 mmHg"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        bp_results = [r for r in results if r.vital_type == "BLOOD_PRESSURE"]
        assert len(bp_results) == 1
        assert bp_results[0].value == Decimal("120")

    def test_heart_rate_extracted(self):
        text = "HR: 72 bpm"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        hr_results = [r for r in results if r.vital_type == "HEART_RATE"]
        assert len(hr_results) == 1
        assert hr_results[0].value == Decimal("72")

    def test_spo2_extracted(self):
        text = "SpO2: 98%"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        spo2_results = [r for r in results if r.vital_type == "SPO2"]
        assert len(spo2_results) == 1
        assert spo2_results[0].value == Decimal("98")

    def test_weight_extracted(self):
        text = "weight: 70 kg"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        weight_results = [r for r in results if r.vital_type == "WEIGHT"]
        assert len(weight_results) == 1
        assert weight_results[0].value == Decimal("70")
        assert weight_results[0].unit == "kg"

    def test_no_vitals_returns_empty(self):
        text = "Patient presents with cough. Prescribed antibiotics."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_vital_type_is_correct(self):
        text = "temperature: 98.6 F\nBMI: 22.5"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        types = {r.vital_type for r in results}
        assert "TEMPERATURE" in types
        assert "BMI" in types

    def test_height_extracted(self):
        text = "height: 175 cm"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        height_results = [r for r in results if r.vital_type == "HEIGHT"]
        assert len(height_results) == 1
        assert height_results[0].value == Decimal("175")
        assert height_results[0].unit == "cm"

    def test_bmi_extracted(self):
        text = "BMI: 24.5"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        bmi_results = [r for r in results if r.vital_type == "BMI"]
        assert len(bmi_results) == 1
        assert bmi_results[0].value == Decimal("24.5")

    def test_temperature_extracted(self):
        text = "temp: 37.0 C"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        temp_results = [r for r in results if r.vital_type == "TEMPERATURE"]
        assert len(temp_results) == 1
        assert temp_results[0].value == Decimal("37.0")

    def test_blood_pressure_diastolic_in_unit(self):
        text = "blood pressure: 130/85"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        bp = [r for r in results if r.vital_type == "BLOOD_PRESSURE"]
        assert len(bp) == 1
        # Diastolic is encoded in unit string since the model has no separate column
        assert "85" in bp[0].unit

    def test_empty_text_returns_empty(self):
        extractor = _make_extractor(raw_text="")
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_pulse_keyword_extracted_as_heart_rate(self):
        text = "pulse: 88 bpm"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        hr_results = [r for r in results if r.vital_type == "HEART_RATE"]
        assert len(hr_results) == 1


# ---------------------------------------------------------------------------
# ORM field assignment
# ---------------------------------------------------------------------------

class TestVitalsOrmFields:
    def test_document_id_set(self):
        text = "HR: 72 bpm"
        doc_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set(self):
        text = "HR: 72 bpm"
        member_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text, member_id=member_id)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].member_id == member_id

    def test_confidence_is_medium(self):
        text = "SpO2: 97%"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].confidence_score == "MEDIUM"


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestVitalsPhiNotLogged:
    def test_vital_value_not_in_logs(self, caplog):
        text = "HR: 72 bpm"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.vitals_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert "72" not in record.getMessage() or "vitals_found" in record.getMessage()

    def test_count_is_logged(self, caplog):
        text = "SpO2: 99%"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.INFO, logger="app.nlp.vitals_extractor"):
            extractor.extract([], uuid.uuid4())
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "vitals_found" in all_log_text or "VitalsExtractor" in all_log_text
