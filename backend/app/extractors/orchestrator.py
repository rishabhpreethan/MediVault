"""Extraction orchestrator: tries pdfminer.six first, falls back to pypdf."""
import logging

from app.extractors.base import ExtractionError, ExtractionResult
from app.extractors.pdfminer_extractor import PdfminerExtractor
from app.extractors.pypdf_extractor import PypdfExtractor

logger = logging.getLogger(__name__)

_pdfminer = PdfminerExtractor()
_pypdf = PypdfExtractor()


def extract_with_fallback(pdf_bytes: bytes) -> ExtractionResult:
    """Attempt extraction with pdfminer.six; fall back to pypdf on failure.

    Strategy:
    1. Try pdfminer.six (primary — higher fidelity for well-formed PDFs).
    2. If pdfminer raises ExtractionError, try pypdf (fallback — handles
       some malformed/encrypted PDFs that pdfminer cannot parse).
    3. If both fail, raise ExtractionError with combined error context.

    Logs only library names and outcome — never document content (PHI rule).
    """
    pdfminer_error: ExtractionError | None = None

    try:
        result = _pdfminer.extract(pdf_bytes)
        logger.info("Extraction succeeded with pdfminer")
        return result
    except ExtractionError as exc:
        pdfminer_error = exc
        logger.warning(
            "pdfminer extraction failed, trying pypdf fallback",
            extra={"pdfminer_error": str(exc)},
        )

    try:
        result = _pypdf.extract(pdf_bytes)
        logger.info("Extraction succeeded with pypdf fallback")
        return result
    except ExtractionError as exc:
        raise ExtractionError(
            f"All extractors failed. pdfminer: {pdfminer_error}. pypdf: {exc}"
        ) from exc
