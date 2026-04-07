"""MV-044: Allergy extractor — regex-based pattern matching for allergy phrases."""
from __future__ import annotations

import logging
import re
import uuid
from typing import List, Optional

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.allergy import Allergy

logger = logging.getLogger(__name__)

# Pattern: common allergy phrasing followed by the allergen text.
# Examples:
#   "allergic to Penicillin"
#   "Allergy: Penicillin"
#   "known allergy to sulfonamides"
#   "hypersensitivity to aspirin"
_ALLERGY_PATTERN = re.compile(
    r"(?:allerg(?:ic\s+to\s+|y\s*:\s*)|hypersensitivity\s+to\s+|known\s+allergy\s+to\s+)"
    r"([A-Za-z][^\n.;,]{2,50})",
    re.IGNORECASE | re.MULTILINE,
)

# Patterns that indicate "no known drug allergies"
_NKDA_PATTERN = re.compile(
    r"\bNKDA\b|no\s+known\s+(?:drug\s+)?allerg",
    re.IGNORECASE,
)

# Maximum length to store in allergen_name column
_MAX_ALLERGEN_LEN = 255


class AllergyExtractor(BaseNlpExtractor):
    """Extract allergies via regex pattern matching.

    Med7 does not provide an ``ALLERGY`` entity label, so this extractor uses a
    regex fallback.  All extracted allergies receive ``confidence_score = "LOW"``
    because they rely solely on regex (no NER confirmation).

    Special case: if "NKDA" or "no known" appears in the text, a single Allergy
    record is created with ``allergen_name="NKDA"`` and ``reaction_type="none"``.

    PHI rule: allergen names are **never** logged — only count and ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.
        raw_text: The plain-text content of the document.
    """

    entity_label: str = "DRUG"  # Placeholder — Med7 has no ALLERGY label

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Run pattern matching over ``raw_text`` and return Allergy ORM instances.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.

        Args:
            entities: Ignored.  Present for interface compatibility with
                :class:`~app.nlp.base_extractor.BaseNlpExtractor`.
            document_id: UUID of the source Document record.

        Returns:
            list[Allergy]: Unsaved ORM instances, one per pattern match (or one
            NKDA record if no-known-allergy phrasing is found).
        """
        allergies: list[Allergy] = []

        # Check for NKDA / no known drug allergies first
        if _NKDA_PATTERN.search(self._raw_text):
            nkda = Allergy(
                member_id=self._member_id,
                document_id=document_id,
                allergen_name="NKDA",
                reaction_type="none",
                confidence_score="LOW",
                is_manual_entry=False,
            )
            allergies.append(nkda)
            # Log only count — never log allergen names (PHI)
            logger.info(
                "AllergyExtractor complete",
                extra={
                    "document_id": str(document_id),
                    "allergies_found": len(allergies),
                    "confidence": "LOW",
                },
            )
            return allergies

        for match in _ALLERGY_PATTERN.finditer(self._raw_text):
            allergen_raw = match.group(1).strip()

            # Truncate to column max
            allergen = allergen_raw[:_MAX_ALLERGEN_LEN]

            if not allergen:
                continue

            allergy = Allergy(
                member_id=self._member_id,
                document_id=document_id,
                allergen_name=allergen,
                reaction_type=None,
                confidence_score="LOW",
                is_manual_entry=False,
            )
            allergies.append(allergy)

        # Log only count — never log allergen names (PHI)
        logger.info(
            "AllergyExtractor complete",
            extra={
                "document_id": str(document_id),
                "allergies_found": len(allergies),
                "confidence": "LOW",
            },
        )

        return allergies
