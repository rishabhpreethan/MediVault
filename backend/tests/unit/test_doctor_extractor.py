"""Unit tests for app.nlp.doctor_extractor — MV-046."""
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
    from app.nlp.doctor_extractor import DoctorExtractor  # noqa: PLC0415
    return DoctorExtractor(member_id=member_id or uuid.uuid4(), raw_text=raw_text)


# ---------------------------------------------------------------------------
# Pattern matching — minimum required tests
# ---------------------------------------------------------------------------

class TestDoctorPatternMatching:
    def test_dr_prefix_matched(self):
        text = "Signed by Dr. Sarah Vance on discharge."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert any("Sarah" in r.doctor_name for r in doctor_results)

    def test_physician_keyword_matched(self):
        text = "Physician: Dr. Emily Rowe"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert any("Emily" in r.doctor_name or "Rowe" in r.doctor_name for r in doctor_results)

    def test_facility_extracted(self):
        text = "Hospital: St Mary Medical Center"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        facility_results = [r for r in results if r.facility_name is not None]
        assert len(facility_results) == 1
        assert "St Mary" in facility_results[0].facility_name

    def test_no_match_returns_empty(self):
        text = "Patient presents with mild fever. Temperature 38.2 C."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert results == []

    def test_confidence_is_low(self):
        text = "Dr. James Park attended the patient."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        assert len(results) >= 1
        assert all(r.confidence_score == "LOW" for r in results)

    def test_partial_name_captured(self):
        text = "Dr. Priya saw the patient today."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert any("Priya" in r.doctor_name for r in doctor_results)

    def test_attending_keyword_matched(self):
        text = "Attending: Dr. Robert Chen"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert any("Robert" in r.doctor_name or "Chen" in r.doctor_name for r in doctor_results)

    def test_referred_to_keyword_matched(self):
        text = "Referred to Dr. Alice Kim for follow-up."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert any("Alice" in r.doctor_name or "Kim" in r.doctor_name for r in doctor_results)

    def test_clinic_facility_extracted(self):
        text = "Clinic: City Health Clinic"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        facility_results = [r for r in results if r.facility_name is not None]
        assert len(facility_results) == 1
        assert "City Health" in facility_results[0].facility_name

    def test_doctor_only_record_has_no_facility(self):
        text = "Dr. Nathan Blake reviewed the labs."
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        doctor_results = [r for r in results if r.doctor_name is not None]
        assert len(doctor_results) >= 1
        assert all(r.facility_name is None for r in doctor_results)

    def test_facility_only_record_has_no_doctor_name(self):
        text = "Facility: Apollo Diagnostics"
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], uuid.uuid4())
        facility_results = [r for r in results if r.facility_name is not None]
        assert len(facility_results) == 1
        assert facility_results[0].doctor_name is None

    def test_empty_text_returns_empty(self):
        extractor = _make_extractor(raw_text="")
        results = extractor.extract([], uuid.uuid4())
        assert results == []


# ---------------------------------------------------------------------------
# ORM field assignment
# ---------------------------------------------------------------------------

class TestDoctorOrmFields:
    def test_document_id_set(self):
        text = "Dr. Sarah Vance"
        doc_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text)
        results = extractor.extract([], doc_id)
        assert results[0].document_id == doc_id

    def test_member_id_set(self):
        text = "Dr. Sarah Vance"
        member_id = uuid.uuid4()
        extractor = _make_extractor(raw_text=text, member_id=member_id)
        results = extractor.extract([], uuid.uuid4())
        assert results[0].member_id == member_id


# ---------------------------------------------------------------------------
# PHI not logged
# ---------------------------------------------------------------------------

class TestDoctorPhiNotLogged:
    def test_doctor_name_not_in_logs(self, caplog):
        secret_name = "TopSecretDoctor_PHI_XYZ_9999"
        text = f"Dr. {secret_name} attended the patient."
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.DEBUG, logger="app.nlp.doctor_extractor"):
            extractor.extract([], uuid.uuid4())
        for record in caplog.records:
            assert secret_name not in record.getMessage()
            assert secret_name not in str(record.__dict__)

    def test_count_is_logged(self, caplog):
        text = "Dr. James Park"
        extractor = _make_extractor(raw_text=text)
        with caplog.at_level(logging.INFO, logger="app.nlp.doctor_extractor"):
            extractor.extract([], uuid.uuid4())
        all_log_text = " ".join(str(r.__dict__) for r in caplog.records)
        assert "doctors_found" in all_log_text or "DoctorExtractor" in all_log_text
