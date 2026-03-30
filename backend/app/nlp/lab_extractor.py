"""MV-042: Lab result extractor — regex-based pattern matching for lab values."""
from __future__ import annotations

import logging
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.lab_result import LabResult

logger = logging.getLogger(__name__)

# Pattern: <test name>: <numeric value> <optional unit>
# Examples:
#   Hemoglobin: 13.5 g/dL
#   WBC: 8200 /uL
#   Glucose: 95 mg/dL
_LAB_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z\s]{1,50}?):\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z/%]+)?",
    re.MULTILINE,
)

# Minimum length for a plausible test name (avoids single-char false positives)
_MIN_TEST_NAME_LEN = 2


class LabExtractor(BaseNlpExtractor):
    """Extract lab results via regex pattern matching.

    Med7 does not provide a ``LAB`` entity label, so this extractor uses a
    regex fallback.  All extracted results receive ``confidence_score = "MEDIUM"``
    because they lack NER confirmation.

    PHI rule: test names and numeric values are **never** logged — only result
    count and ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.
        raw_text: The plain-text content of the document.  The ``entities``
            argument passed to :meth:`extract` is accepted but unused; the
            regex runs over the raw text instead.
    """

    entity_label: str = "DRUG"  # Placeholder — Med7 has no LAB label

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Run regex over ``raw_text`` and return LabResult ORM instances.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.

        Args:
            entities: Ignored.  Present for interface compatibility with
                :class:`~app.nlp.base_extractor.BaseNlpExtractor`.
            document_id: UUID of the source Document record.

        Returns:
            list[LabResult]: Unsaved ORM instances, one per regex match.
        """
        results: list[LabResult] = []

        for match in _LAB_PATTERN.finditer(self._raw_text):
            test_name_raw = match.group(1).strip()
            value_str = match.group(2).strip()
            unit_raw: Optional[str] = match.group(3)
            unit = unit_raw.strip() if unit_raw else None

            # Skip implausibly short test names
            if len(test_name_raw) < _MIN_TEST_NAME_LEN:
                continue

            # Parse value as Decimal for the Numeric(12,4) column
            try:
                value = Decimal(value_str)
            except InvalidOperation:
                continue  # Malformed numeric — skip

            lab = LabResult(
                member_id=self._member_id,
                document_id=document_id,
                test_name=test_name_raw,
                value=value,
                value_text=value_str,
                unit=unit,
                confidence_score="MEDIUM",
                is_manual_entry=False,
            )
            results.append(lab)

        # Log only count — never log test names or values (PHI)
        logger.info(
            "LabExtractor complete",
            extra={
                "document_id": str(document_id),
                "labs_found": len(results),
                "confidence": "MEDIUM",
            },
        )

        return results
