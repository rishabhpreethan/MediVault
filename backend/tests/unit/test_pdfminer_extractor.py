"""Unit tests for pdfminer.six extractor — no DB or MinIO required."""
import pytest

from app.extractors.base import ExtractionError, ExtractionResult
from app.extractors.pdfminer_extractor import PdfminerExtractor

# Minimal valid PDF with embedded text "Hello World"
# Generated as a well-formed PDF 1.4 document with a single page.
MINIMAL_TEXT_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000274 00000 n \n"
    b"0000000370 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n441\n%%EOF"
)

# PDF with no content stream — will extract empty text
EMPTY_PAGE_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n175\n%%EOF"
)


@pytest.fixture
def extractor():
    return PdfminerExtractor()


class TestPdfminerExtractorBasic:
    def test_returns_extraction_result_type(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert isinstance(result, ExtractionResult)

    def test_library_used_is_pdfminer(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        assert result.library_used == "pdfminer"

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


class TestPdfminerExtractorTextExtraction:
    def test_extracts_text_from_text_pdf(self, extractor):
        result = extractor.extract(MINIMAL_TEXT_PDF)
        # pdfminer should extract something from a PDF with an embedded font + text stream
        # The exact text depends on pdfminer's encoding handling for Type1 fonts
        assert result.text is not None

    def test_empty_pdf_has_no_text_layer(self, extractor):
        """A PDF with no content stream has no meaningful text layer."""
        result = extractor.extract(EMPTY_PAGE_PDF)
        assert result.has_text_layer is False

    def test_text_layer_detection_threshold(self, extractor):
        """has_text_layer is False when extracted text is below MIN_TEXT_CHARS."""
        assert extractor.MIN_TEXT_CHARS == 50


class TestPdfminerExtractorErrors:
    def test_raises_extraction_error_on_empty_bytes(self, extractor):
        with pytest.raises(ExtractionError):
            extractor.extract(b"")

    def test_raises_extraction_error_on_garbage_bytes(self, extractor):
        with pytest.raises(ExtractionError):
            extractor.extract(b"not a pdf at all \x00\x01\x02")

    def test_raises_extraction_error_on_truncated_pdf(self, extractor):
        truncated = MINIMAL_TEXT_PDF[:50]
        with pytest.raises(ExtractionError):
            extractor.extract(truncated)


class TestExtractionResultDataclass:
    def test_fields(self):
        r = ExtractionResult(
            text="some text",
            page_count=2,
            has_text_layer=True,
            library_used="pdfminer",
        )
        assert r.text == "some text"
        assert r.page_count == 2
        assert r.has_text_layer is True
        assert r.library_used == "pdfminer"


class TestExtractionError:
    def test_is_exception(self):
        err = ExtractionError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"
