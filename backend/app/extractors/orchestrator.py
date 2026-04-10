"""Extraction orchestrator: tries pdfminer.six first, falls back to pypdf."""
from __future__ import annotations

import logging
from typing import Optional

from app.extractors.base import ExtractionError, ExtractionResult
from app.extractors.pdfminer_extractor import PdfminerExtractor
from app.extractors.pypdf_extractor import PypdfExtractor

logger = logging.getLogger(__name__)

_pdfminer = PdfminerExtractor()
_pypdf = PypdfExtractor()

# Characters-per-page threshold below which a PDF is considered likely scanned
_CHARS_PER_PAGE_THRESHOLD = 50
# Absolute minimum characters; below this the PDF is certainly not text-bearing
_MIN_ABSOLUTE_CHARS = 100


def is_likely_scanned(text: str, page_count: int) -> bool:
    """Return True if the extracted text suggests a scanned (image-only) PDF.

    Heuristics applied in order:
    1. Fewer than 100 characters total → almost nothing extracted → scanned.
    2. page_count > 0 and chars-per-page < 50 → sparse text → scanned.
    3. Otherwise → not scanned.

    Args:
        text: Extracted text string (may be empty).
        page_count: Number of pages reported by the PDF reader.
                    When 0 the per-page heuristic is skipped.

    Returns:
        True if the PDF is likely scanned, False otherwise.
    """
    char_count = len(text.strip())

    if char_count < _MIN_ABSOLUTE_CHARS:
        return True

    if page_count > 0 and char_count / page_count < _CHARS_PER_PAGE_THRESHOLD:
        return True

    return False


def extract_with_fallback(
    pdf_bytes: bytes,
    page_count: int = 0,
) -> ExtractionResult:
    """Attempt extraction with pdfminer.six; fall back to pypdf on failure.

    Strategy:
    1. Try pdfminer.six (primary — higher fidelity for well-formed PDFs).
    2. If pdfminer raises ExtractionError, try pypdf (fallback — handles
       some malformed/encrypted PDFs that pdfminer cannot parse).
    3. If both fail, raise ExtractionError with combined error context.
    4. After successful extraction, run scanned-document heuristic.
       If the PDF appears to be image-only, set has_text_layer = False
       regardless of what the individual extractor reported.

    Logs only library names and outcome — never document content (PHI rule).

    Args:
        pdf_bytes: Raw PDF bytes to extract text from.
        page_count: Page count obtained before extraction (e.g. via pypdf
                    PdfReader). Used to compute chars-per-page heuristic.
                    Defaults to 0 (heuristic falls back to absolute threshold).
    """
    pdfminer_error: Optional[ExtractionError] = None

    try:
        result = _pdfminer.extract(pdf_bytes)
        logger.info("Extraction succeeded with pdfminer")
    except ExtractionError as exc:
        pdfminer_error = exc
        logger.warning(
            "pdfminer extraction failed, trying pypdf fallback",
            extra={"pdfminer_error": str(exc)},
        )

        try:
            result = _pypdf.extract(pdf_bytes)
            logger.info("Extraction succeeded with pypdf fallback")
        except ExtractionError as exc2:
            raise ExtractionError(
                f"All extractors failed. pdfminer: {pdfminer_error}. pypdf: {exc2}"
            ) from exc2

    # Scanned-document detection: override has_text_layer if the text is
    # too sparse to be a real digital PDF.
    if is_likely_scanned(result.text, page_count):
        result = ExtractionResult(
            text=result.text,
            page_count=result.page_count,
            has_text_layer=False,
            library_used=result.library_used,
        )
        logger.info(
            "Scanned document detected by heuristic",
            extra={
                "page_count": page_count,
                "char_count": len(result.text.strip()),
                "library_used": result.library_used,
            },
        )

    return result
