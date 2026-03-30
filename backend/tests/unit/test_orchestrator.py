"""Unit tests for extraction orchestrator."""
from unittest.mock import patch, MagicMock

import pytest

from app.extractors.base import ExtractionError, ExtractionResult
from app.extractors.orchestrator import extract_with_fallback
from tests.unit.test_pdfminer_extractor import MINIMAL_TEXT_PDF, EMPTY_PAGE_PDF

_PDFMINER_RESULT = ExtractionResult(
    text="extracted text",
    page_count=1,
    has_text_layer=True,
    library_used="pdfminer",
)
_PYPDF_RESULT = ExtractionResult(
    text="fallback text",
    page_count=1,
    has_text_layer=True,
    library_used="pypdf",
)


class TestOrchestratorSuccess:
    def test_returns_pdfminer_result_on_success(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm:
            mock_pm.extract.return_value = _PDFMINER_RESULT
            result = extract_with_fallback(MINIMAL_TEXT_PDF)
        assert result.library_used == "pdfminer"
        assert result.text == "extracted text"

    def test_pdfminer_called_first(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.return_value = _PDFMINER_RESULT
            extract_with_fallback(MINIMAL_TEXT_PDF)
        mock_pm.extract.assert_called_once()
        mock_py.extract.assert_not_called()

    def test_pypdf_not_called_when_pdfminer_succeeds(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.return_value = _PDFMINER_RESULT
            extract_with_fallback(b"any bytes")
        mock_py.extract.assert_not_called()


class TestOrchestratorFallback:
    def test_falls_back_to_pypdf_on_pdfminer_failure(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.side_effect = ExtractionError("pdfminer failed")
            mock_py.extract.return_value = _PYPDF_RESULT
            result = extract_with_fallback(MINIMAL_TEXT_PDF)
        assert result.library_used == "pypdf"

    def test_pypdf_called_after_pdfminer_failure(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.side_effect = ExtractionError("pdfminer failed")
            mock_py.extract.return_value = _PYPDF_RESULT
            extract_with_fallback(b"any bytes")
        mock_py.extract.assert_called_once()

    def test_raises_extraction_error_when_both_fail(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.side_effect = ExtractionError("pdfminer failed")
            mock_py.extract.side_effect = ExtractionError("pypdf also failed")
            with pytest.raises(ExtractionError) as exc_info:
                extract_with_fallback(b"broken pdf")
        assert "pdfminer" in str(exc_info.value)
        assert "pypdf" in str(exc_info.value)

    def test_combined_error_message_includes_both_errors(self):
        with patch("app.extractors.orchestrator._pdfminer") as mock_pm, \
             patch("app.extractors.orchestrator._pypdf") as mock_py:
            mock_pm.extract.side_effect = ExtractionError("pdfminer: bad xref")
            mock_py.extract.side_effect = ExtractionError("pypdf: encrypted")
            with pytest.raises(ExtractionError) as exc_info:
                extract_with_fallback(b"bad pdf")
        msg = str(exc_info.value)
        assert "bad xref" in msg
        assert "encrypted" in msg


class TestOrchestratorIntegration:
    """Integration-style tests against real PDF bytes (no mocks)."""

    def test_extracts_valid_pdf(self):
        result = extract_with_fallback(MINIMAL_TEXT_PDF)
        assert isinstance(result, ExtractionResult)
        assert result.library_used in ("pdfminer", "pypdf")

    def test_raises_on_garbage_bytes(self):
        with pytest.raises(ExtractionError):
            extract_with_fallback(b"not a pdf at all")
