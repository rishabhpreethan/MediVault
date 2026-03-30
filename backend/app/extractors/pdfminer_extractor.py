import io
import logging

from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from app.extractors.base import BaseExtractor, ExtractionError, ExtractionResult

logger = logging.getLogger(__name__)


class PdfminerExtractor(BaseExtractor):
    """Primary PDF extractor using pdfminer.six."""

    def extract(self, pdf_bytes: bytes) -> ExtractionResult:
        """Extract text from PDF bytes using pdfminer.six.

        Logs only character count and page count — never the extracted content.

        Raises:
            ExtractionError: If pdfminer fails to parse or extract the PDF.
        """
        if not pdf_bytes:
            raise ExtractionError("PDF bytes are empty")

        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            page_count = self._count_pages(pdf_stream)

            pdf_stream.seek(0)
            laparams = LAParams(line_margin=0.5, word_margin=0.1)
            text = extract_text(pdf_stream, laparams=laparams)
        except PDFSyntaxError as exc:
            raise ExtractionError(f"PDF syntax error: {exc}") from exc
        except Exception as exc:
            raise ExtractionError(f"pdfminer extraction failed: {exc}") from exc

        text = text or ""
        has_text_layer = len(text.strip()) >= self.MIN_TEXT_CHARS

        # Log only metadata, never the text content itself (PHI rule)
        logger.info(
            "pdfminer extraction complete",
            extra={
                "page_count": page_count,
                "char_count": len(text),
                "has_text_layer": has_text_layer,
            },
        )

        return ExtractionResult(
            text=text,
            page_count=page_count,
            has_text_layer=has_text_layer,
            library_used="pdfminer",
        )

    def _count_pages(self, pdf_stream: io.BytesIO) -> int:
        try:
            return sum(1 for _ in PDFPage.get_pages(pdf_stream))
        except Exception:
            return 0
