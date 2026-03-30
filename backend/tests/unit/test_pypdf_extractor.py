"""Unit tests for pypdf fallback extractor."""
import pytest

from app.extractors.base import ExtractionError, ExtractionResult
from app.extractors.pypdf_extractor import PypdfExtractor
from tests.unit.test_pdfminer_extractor import MINIMAL_TEXT_PDF, EMPTY_PAGE_PDF


@pytest.fixture
def extractor():
    return PypdfExtractor()


class TestPypdfExtractorBasic:
    def test_returns_extraction_result_type(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert isinstance(result, ExtractionResult)

    def test_library_used_is_pypdf(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert result.library_used == "pypdf"

    def test_text_is_string(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert isinstance(result.text, str)

    def test_page_count_is_int(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert isinstance(result.page_count, int)
        assert result.page_count >= 0

    def test_has_text_layer_is_bool(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert isinstance(result.has_text_layer, bool)


class TestPypdfExtractorErrors:
    def test_raises_extraction_error_on_empty_bytes(self, extractor):
        with pytest.raises(ExtractionError):
            extractor.extract(b"")

    def test_raises_extraction_error_on_garbage_bytes(self, extractor):
        with pytest.raises(ExtractionError):
            extractor.extract(b"this is not a pdf \x00\x01\x02")

    def test_empty_pdf_has_no_text_layer(self, extractor):
        result = extractor.extract(EMPTY_PAGE_PDF)
        assert result.has_text_layer is False
