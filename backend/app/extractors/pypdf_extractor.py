import io
import logging
from typing import Optional

from app.extractors.base import BaseExtractor, ExtractionError, ExtractionResult

logger = logging.getLogger(__name__)


class PypdfExtractor(BaseExtractor):
    """Fallback PDF extractor using pypdf."""

    def extract(self, pdf_bytes: bytes) -> ExtractionResult:
        """Extract text from PDF bytes using pypdf.

        Logs only character count and page count — never the extracted content.

        Raises:
            ExtractionError: If pypdf fails to parse or extract the PDF.
        """
        if not pdf_bytes:
            raise ExtractionError("PDF bytes are empty")

        try:
            from pypdf import PdfReader  # noqa: PLC0415 — lazy import (optional dep)
            from pypdf.errors import PdfReadError  # noqa: PLC0415
        except ImportError as exc:
            raise ExtractionError("pypdf is not installed") from exc

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(reader.pages)
            text_parts: list[str] = []
            for page in reader.pages:
                page_text: Optional[str] = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            text = "\n".join(text_parts)
        except Exception as exc:
            raise ExtractionError(f"pypdf extraction failed: {exc}") from exc

        text = text or ""
        has_text_layer = len(text.strip()) >= self.MIN_TEXT_CHARS

        logger.info(
            "pypdf extraction complete",
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
            library_used="pypdf",
        )
