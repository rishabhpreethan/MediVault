from abc import ABC, abstractmethod
from dataclasses import dataclass


class ExtractionError(Exception):
    """Raised when PDF text extraction fails."""


@dataclass
class ExtractionResult:
    text: str
    page_count: int
    has_text_layer: bool
    library_used: str  # "pdfminer" | "pypdf"


class BaseExtractor(ABC):
    """Abstract base for PDF text extractors."""

    # Minimum character count to consider a PDF as having a real text layer
    MIN_TEXT_CHARS = 50

    @abstractmethod
    def extract(self, pdf_bytes: bytes) -> ExtractionResult:
        """Extract text from raw PDF bytes.

        Args:
            pdf_bytes: Raw bytes of a PDF file.

        Returns:
            ExtractionResult with extracted text and metadata.

        Raises:
            ExtractionError: If extraction fails.
        """
        ...
