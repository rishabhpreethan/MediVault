"""Unit tests for app.nlp.pipeline — spaCy/Med7 pipeline loading and entity extraction."""
from __future__ import annotations

import importlib
import logging
import sys
import uuid
from types import ModuleType
from typing import List
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Inject a fake 'spacy' module into sys.modules so tests work without spaCy
# installed locally. The real spaCy is only available inside Docker.
# ---------------------------------------------------------------------------
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy


# ---------------------------------------------------------------------------
# Helpers to build a minimal fake spaCy span / doc
# ---------------------------------------------------------------------------

def _make_fake_ent(text: str, label: str, start_char: int, end_char: int) -> MagicMock:
    ent = MagicMock()
    ent.text = text
    ent.label_ = label
    ent.start_char = start_char
    ent.end_char = end_char
    return ent


def _make_fake_doc(ents: list) -> MagicMock:
    doc = MagicMock()
    doc.ents = ents
    return doc


def _make_fake_nlp(ents: list) -> MagicMock:
    """Return a mock spaCy Language that produces *ents* when called."""
    nlp = MagicMock()
    nlp.return_value = _make_fake_doc(ents)
    return nlp


# ---------------------------------------------------------------------------
# Reload pipeline module with a clean singleton for each test
# ---------------------------------------------------------------------------

def _reload_pipeline():
    """Force-reload app.nlp.pipeline so the _nlp singleton is reset."""
    if "app.nlp.pipeline" in sys.modules:
        del sys.modules["app.nlp.pipeline"]
    import app.nlp.pipeline as pipeline_mod  # noqa: PLC0415
    return pipeline_mod


# ---------------------------------------------------------------------------
# Tests: extract_entities output shape
# ---------------------------------------------------------------------------

class TestExtractEntitiesShape:
    def test_returns_list_of_dicts(self):
        ents = [_make_fake_ent("Aspirin", "DRUG", 0, 7)]
        pipeline_mod = _reload_pipeline()
        with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
            result = pipeline_mod.extract_entities("Aspirin 100mg")
        assert isinstance(result, list)
        assert len(result) == 1

    def test_dict_has_required_keys(self):
        ents = [_make_fake_ent("Aspirin", "DRUG", 0, 7)]
        pipeline_mod = _reload_pipeline()
        with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
            result = pipeline_mod.extract_entities("Aspirin 100mg")
        entity = result[0]
        assert "text" in entity
        assert "label" in entity
        assert "start" in entity
        assert "end" in entity

    def test_entity_values_are_correct(self):
        ents = [_make_fake_ent("Ibuprofen", "DRUG", 5, 14)]
        pipeline_mod = _reload_pipeline()
        with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
            result = pipeline_mod.extract_entities("Take Ibuprofen 200mg")
        assert result[0]["text"] == "Ibuprofen"
        assert result[0]["label"] == "DRUG"
        assert result[0]["start"] == 5
        assert result[0]["end"] == 14

    def test_empty_text_returns_empty_list(self):
        pipeline_mod = _reload_pipeline()
        with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp([])):
            result = pipeline_mod.extract_entities("")
        assert result == []

    def test_multiple_entities_returned(self):
        ents = [
            _make_fake_ent("Aspirin", "DRUG", 0, 7),
            _make_fake_ent("100mg", "DOSAGE", 8, 13),
            _make_fake_ent("twice daily", "FREQUENCY", 14, 25),
        ]
        pipeline_mod = _reload_pipeline()
        with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
            result = pipeline_mod.extract_entities("Aspirin 100mg twice daily")
        assert len(result) == 3
        labels = {e["label"] for e in result}
        assert labels == {"DRUG", "DOSAGE", "FREQUENCY"}


# ---------------------------------------------------------------------------
# Tests: PHI is not logged
# ---------------------------------------------------------------------------

class TestPhiNotLogged:
    def test_entity_text_not_in_log_output(self, caplog):
        """Entity surface text must never appear in log records."""
        secret_text = "SuperSecretDrugName_XYZ_9999"
        ents = [_make_fake_ent(secret_text, "DRUG", 0, len(secret_text))]
        pipeline_mod = _reload_pipeline()
        with caplog.at_level(logging.DEBUG, logger="app.nlp.pipeline"):
            with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
                pipeline_mod.extract_entities(secret_text)
        # None of the log messages should contain the PHI text
        for record in caplog.records:
            assert secret_text not in record.getMessage()
            # Also check the extra dict serialized into the record
            assert secret_text not in str(record.__dict__)

    def test_label_counts_are_logged(self, caplog):
        """Label counts (not text) should appear in log output."""
        ents = [_make_fake_ent("Aspirin", "DRUG", 0, 7)]
        pipeline_mod = _reload_pipeline()
        with caplog.at_level(logging.INFO, logger="app.nlp.pipeline"):
            with patch.object(pipeline_mod, "get_nlp", return_value=_make_fake_nlp(ents)):
                pipeline_mod.extract_entities("Aspirin")
        combined = " ".join(r.getMessage() for r in caplog.records)
        # The log must mention the label, not the entity text
        assert "DRUG" in combined or any("DRUG" in str(r.__dict__) for r in caplog.records)


# ---------------------------------------------------------------------------
# Tests: lazy singleton — get_nlp called multiple times returns same object
# ---------------------------------------------------------------------------

class TestLazySingleton:
    def test_get_nlp_returns_same_object_on_repeated_calls(self):
        pipeline_mod = _reload_pipeline()
        fake_nlp = _make_fake_nlp([])
        with patch("spacy.load", return_value=fake_nlp) as mock_load:
            first = pipeline_mod.get_nlp()
            second = pipeline_mod.get_nlp()
            third = pipeline_mod.get_nlp()
        # spacy.load should only be called once regardless of how many times we call get_nlp
        assert mock_load.call_count == 1
        assert first is second
        assert second is third

    def test_get_nlp_object_identity_preserved(self):
        pipeline_mod = _reload_pipeline()
        fake_nlp = _make_fake_nlp([])
        with patch("spacy.load", return_value=fake_nlp):
            result_a = pipeline_mod.get_nlp()
            result_b = pipeline_mod.get_nlp()
        assert result_a is result_b


# ---------------------------------------------------------------------------
# Tests: fallback when Med7 model is not available
# ---------------------------------------------------------------------------

class TestMed7Fallback:
    def test_falls_back_to_en_core_web_sm_when_med7_missing(self):
        pipeline_mod = _reload_pipeline()
        fallback_nlp = _make_fake_nlp([])

        def spacy_load_side_effect(model_name):
            if model_name == "en_core_med7_lg":
                raise OSError("Model not found")
            return fallback_nlp

        with patch("spacy.load", side_effect=spacy_load_side_effect) as mock_load:
            result = pipeline_mod.get_nlp()

        assert result is fallback_nlp
        # Should have tried Med7 first, then fallen back
        calls = [c.args[0] for c in mock_load.call_args_list]
        assert "en_core_med7_lg" in calls
        assert "en_core_web_sm" in calls

    def test_fallback_logs_warning(self, caplog):
        pipeline_mod = _reload_pipeline()
        fallback_nlp = _make_fake_nlp([])

        def spacy_load_side_effect(model_name):
            if model_name == "en_core_med7_lg":
                raise OSError("Model not found")
            return fallback_nlp

        with caplog.at_level(logging.WARNING, logger="app.nlp.pipeline"):
            with patch("spacy.load", side_effect=spacy_load_side_effect):
                pipeline_mod.get_nlp()

        warning_messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("Med7" in msg or "med7" in msg or "fallback" in msg.lower() for msg in warning_messages)

    def test_extract_entities_works_with_fallback_pipeline(self):
        pipeline_mod = _reload_pipeline()
        fallback_ents = [_make_fake_ent("hospital", "ORG", 0, 8)]
        fallback_nlp = _make_fake_nlp(fallback_ents)

        def spacy_load_side_effect(model_name):
            if model_name == "en_core_med7_lg":
                raise OSError("Model not found")
            return fallback_nlp

        with patch("spacy.load", side_effect=spacy_load_side_effect):
            result = pipeline_mod.extract_entities("Patient discharged from hospital")

        assert len(result) == 1
        assert result[0]["label"] == "ORG"

    def test_singleton_preserved_after_fallback(self):
        """Once fallback is loaded, subsequent calls must not reload."""
        pipeline_mod = _reload_pipeline()
        fallback_nlp = _make_fake_nlp([])

        def spacy_load_side_effect(model_name):
            if model_name == "en_core_med7_lg":
                raise OSError("Model not found")
            return fallback_nlp

        with patch("spacy.load", side_effect=spacy_load_side_effect) as mock_load:
            pipeline_mod.get_nlp()
            pipeline_mod.get_nlp()
            pipeline_mod.get_nlp()

        # Two loads: one attempt for Med7 (OSError), one for en_core_web_sm
        assert mock_load.call_count == 2


# ---------------------------------------------------------------------------
# Tests: BaseNlpExtractor ABC
# ---------------------------------------------------------------------------

class TestBaseNlpExtractor:
    def test_cannot_instantiate_abstract_class(self):
        from app.nlp.base_extractor import BaseNlpExtractor  # noqa: PLC0415
        import pytest as _pytest  # noqa: PLC0415
        with _pytest.raises(TypeError):
            BaseNlpExtractor()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_extract(self):
        from app.nlp.base_extractor import BaseNlpExtractor  # noqa: PLC0415

        class ConcreteExtractor(BaseNlpExtractor):
            entity_label = "DRUG"

            def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
                return [e for e in entities if e["label"] == self.entity_label]

        extractor = ConcreteExtractor()
        sample_entities = [
            {"text": "Aspirin", "label": "DRUG", "start": 0, "end": 7},
            {"text": "100mg", "label": "DOSAGE", "start": 8, "end": 13},
        ]
        result = extractor.extract(sample_entities, uuid.uuid4())
        assert len(result) == 1
        assert result[0]["label"] == "DRUG"

    def test_entity_label_class_attribute_accessible(self):
        from app.nlp.base_extractor import BaseNlpExtractor  # noqa: PLC0415

        class DosageExtractor(BaseNlpExtractor):
            entity_label = "DOSAGE"

            def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
                return []

        assert DosageExtractor.entity_label == "DOSAGE"
        assert DosageExtractor().entity_label == "DOSAGE"
