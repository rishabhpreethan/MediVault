"""MV-046: Doctor extractor — regex-based pattern matching for doctor and facility names."""
from __future__ import annotations

import logging
import re
import uuid
from typing import List, Optional

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.doctor import Doctor

logger = logging.getLogger(__name__)

# Pattern 1: "Dr. Sarah Vance" or "Doctor John Smith"
_DR_PREFIX_PATTERN = re.compile(
    r"(?:Dr\.?\s+|Doctor\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
)

# Pattern 2: Clinical role keywords followed by an optional Dr prefix and a name
# Examples:
#   "Physician: Dr. Emily Rowe"
#   "Attending: Dr. James Park"
#   "Consultant: Dr. Priya Mehta"
#   "Referred to Dr. Rachel Burns"
#   "Referred by Dr. Brian Cho"
_ROLE_PATTERN = re.compile(
    r"(?:Physician|Attending|Consultant|Referred\s+(?:to|by))[:\s]+(?:Dr\.?\s+)?"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
)

# Pattern 3: Facility / Hospital / Clinic names
# Examples:
#   "Hospital: St. Mary's Medical Center"
#   "Facility: Apollo Diagnostics"
#   "Clinic: City Health Clinic"
_FACILITY_PATTERN = re.compile(
    r"(?:Facility|Hospital|Clinic)[:\s]+([A-Za-z][^\n.;]{3,60})",
)

# Maximum length for name columns
_MAX_NAME_LEN = 255


class DoctorExtractor(BaseNlpExtractor):
    """Extract doctor names and facility names via regex pattern matching.

    Med7 does not provide a ``DOCTOR`` entity label, so this extractor uses a
    regex fallback.  All extracted records receive ``confidence_score = "LOW"``
    because they rely solely on regex (no NER confirmation).

    PHI rule: doctor names are **never** logged — only count and ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.
        raw_text: The plain-text content of the document.
    """

    entity_label: str = "DRUG"  # Placeholder — Med7 has no DOCTOR label

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    def _make_doctor(
        self,
        document_id: uuid.UUID,
        doctor_name: Optional[str],
        facility_name: Optional[str],
    ) -> Doctor:
        return Doctor(
            member_id=self._member_id,
            document_id=document_id,
            doctor_name=doctor_name[:_MAX_NAME_LEN] if doctor_name else None,
            facility_name=facility_name[:_MAX_NAME_LEN] if facility_name else None,
            confidence_score="LOW",
        )

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Run pattern matching over ``raw_text`` and return Doctor ORM instances.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.

        Args:
            entities: Ignored.  Present for interface compatibility with
                :class:`~app.nlp.base_extractor.BaseNlpExtractor`.
            document_id: UUID of the source Document record.

        Returns:
            list[Doctor]: Unsaved ORM instances, one per pattern match.
        """
        doctors: list[Doctor] = []

        # Doctor name patterns (Dr. prefix and role keyword patterns)
        for match in _DR_PREFIX_PATTERN.finditer(self._raw_text):
            name = match.group(1).strip()
            if name:
                doctors.append(self._make_doctor(document_id, name, None))

        for match in _ROLE_PATTERN.finditer(self._raw_text):
            name = match.group(1).strip()
            if name:
                doctors.append(self._make_doctor(document_id, name, None))

        # Facility patterns
        for match in _FACILITY_PATTERN.finditer(self._raw_text):
            facility = match.group(1).strip()
            if facility:
                doctors.append(self._make_doctor(document_id, None, facility))

        # Log only count — never log doctor or facility names (PHI)
        logger.info(
            "DoctorExtractor complete",
            extra={
                "document_id": str(document_id),
                "doctors_found": len(doctors),
                "confidence": "LOW",
            },
        )

        return doctors
