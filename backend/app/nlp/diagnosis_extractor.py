"""MV-043: Diagnosis extractor — keyword/pattern matching for diagnostic phrases."""
from __future__ import annotations

import logging
import re
import uuid
from typing import List

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.diagnosis import Diagnosis

logger = logging.getLogger(__name__)

# Pattern: common clinical phrasing followed by the condition text.
# Captures up to 60 non-newline, non-semicolon characters after the trigger.
# Examples:
#   "diagnosed with Type 2 Diabetes Mellitus"
#   "Impression: Bilateral pneumonia"
#   "Assessment: Hypertension, uncontrolled"
#   "Diagnosis: Iron deficiency anemia"
_DIAGNOSIS_PATTERN = re.compile(
    r"(?:diagnosed\s+with\s+|impression\s*:\s*|assessment\s*:\s*|diagnosis\s*:\s*)"
    r"([A-Za-z][^\n.;]{3,60})",
    re.IGNORECASE | re.MULTILINE,
)

# Maximum length to accept after trimming (guards against overly long captures)
_MAX_CONDITION_LEN = 255


class DiagnosisExtractor(BaseNlpExtractor):
    """Extract diagnoses via keyword/pattern matching.

    Med7 does not provide a ``DIAGNOSIS`` entity label, so this extractor uses
    a regex fallback.  All results receive ``confidence_score = "LOW"`` because
    they rely solely on regex (no NER confirmation).

    PHI rule: condition text is **never** logged — only result count and
    ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.
        raw_text: The plain-text content of the document.
    """

    entity_label: str = "DRUG"  # Placeholder — Med7 has no DIAGNOSIS label

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Run keyword/pattern matching over ``raw_text`` and return Diagnosis ORM instances.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.

        Args:
            entities: Ignored.  Present for interface compatibility with
                :class:`~app.nlp.base_extractor.BaseNlpExtractor`.
            document_id: UUID of the source Document record.

        Returns:
            list[Diagnosis]: Unsaved ORM instances, one per pattern match.
        """
        diagnoses: list[Diagnosis] = []

        for match in _DIAGNOSIS_PATTERN.finditer(self._raw_text):
            condition_raw = match.group(1).strip()

            # Truncate to column max just in case the regex captures too much
            condition = condition_raw[:_MAX_CONDITION_LEN]

            if not condition:
                continue

            diag = Diagnosis(
                member_id=self._member_id,
                document_id=document_id,
                condition_name=condition,
                confidence_score="LOW",
                status="UNKNOWN",
                is_manual_entry=False,
            )
            diagnoses.append(diag)

        # Log only count — never log condition names (PHI)
        logger.info(
            "DiagnosisExtractor complete",
            extra={
                "document_id": str(document_id),
                "diagnoses_found": len(diagnoses),
                "confidence": "LOW",
            },
        )

        return diagnoses
