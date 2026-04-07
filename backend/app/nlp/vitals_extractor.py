"""MV-045: Vitals extractor — regex-based pattern matching for vital sign values."""
from __future__ import annotations

import logging
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.vital import Vital

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled vital-sign patterns
# Each entry: (vital_type, compiled_pattern, value_group, unit_group_or_None)
# ---------------------------------------------------------------------------

# Blood pressure: "BP: 120/80" or "blood pressure: 120/80 mmHg"
_BP_PATTERN = re.compile(
    r"(?:BP|blood\s+pressure)[:\s]+(\d{2,3})\s*/\s*(\d{2,3})",
    re.IGNORECASE,
)

# Heart rate / pulse: "HR: 72 bpm" or "pulse: 88 /min"
_HR_PATTERN = re.compile(
    r"(?:HR|heart\s+rate|pulse)[:\s]+(\d{2,3})\s*(?:bpm|/min)?",
    re.IGNORECASE,
)

# Temperature: "temp: 98.6 F" or "temperature: 37.0 C"
_TEMP_PATTERN = re.compile(
    r"(?:temp(?:erature)?)[:\s]+(\d{2,3}(?:\.\d)?)\s*(?:°?([CF]))?",
    re.IGNORECASE,
)

# Weight: "weight: 70.5 kg" or "wt: 155 lbs"
_WEIGHT_PATTERN = re.compile(
    r"(?:weight|wt)[:\s]+(\d{2,3}(?:\.\d)?)\s*(kg|lbs?|lb)",
    re.IGNORECASE,
)

# Height: "height: 175 cm" or "ht: 5'11""
_HEIGHT_PATTERN = re.compile(
    r"(?:height|ht)[:\s]+(\d{1,3}(?:\.\d)?)\s*(cm|m|ft|in|'|\")",
    re.IGNORECASE,
)

# SpO2 / oxygen saturation: "SpO2: 98%" or "O2 saturation: 97 %"
_SPO2_PATTERN = re.compile(
    r"(?:SpO2|O2\s+sat(?:uration)?)[:\s]+(\d{2,3})\s*%?",
    re.IGNORECASE,
)

# BMI: "BMI: 22.5"
_BMI_PATTERN = re.compile(
    r"(?:BMI)[:\s]+(\d{2,3}(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def _to_decimal(value_str: str) -> Optional[Decimal]:
    """Convert a string to Decimal, returning None on failure."""
    try:
        return Decimal(value_str)
    except InvalidOperation:
        return None


class VitalsExtractor(BaseNlpExtractor):
    """Extract vital signs via regex pattern matching.

    Med7 does not provide a ``VITAL`` entity label, so this extractor uses a
    regex fallback.  All extracted vitals receive ``confidence_score = "MEDIUM"``
    because structured numeric patterns carry higher confidence than open-ended
    text triggers.

    Supported vital types: BLOOD_PRESSURE, HEART_RATE, TEMPERATURE, WEIGHT,
    HEIGHT, SPO2, BMI.

    PHI rule: vital values are **never** logged — only count and ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.
        raw_text: The plain-text content of the document.
    """

    entity_label: str = "DRUG"  # Placeholder — Med7 has no VITAL label

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_vital(
        self,
        document_id: uuid.UUID,
        vital_type: str,
        value: Decimal,
        unit: Optional[str],
    ) -> Vital:
        return Vital(
            member_id=self._member_id,
            document_id=document_id,
            vital_type=vital_type,
            value=value,
            unit=unit,
            confidence_score="MEDIUM",
        )

    def _extract_bp(self, document_id: uuid.UUID) -> List[Vital]:
        vitals: List[Vital] = []
        for match in _BP_PATTERN.finditer(self._raw_text):
            systolic = _to_decimal(match.group(1))
            diastolic_str = match.group(2)
            if systolic is None:
                continue
            # Store systolic in value; encode diastolic in unit string so
            # no information is lost without requiring schema changes.
            unit = f"mmHg (diastolic: {diastolic_str})"
            vitals.append(self._make_vital(document_id, "BLOOD_PRESSURE", systolic, unit))
        return vitals

    def _extract_single(
        self,
        document_id: uuid.UUID,
        pattern: re.Pattern,  # type: ignore[type-arg]
        vital_type: str,
        value_group: int = 1,
        unit_group: Optional[int] = None,
        default_unit: Optional[str] = None,
    ) -> List[Vital]:
        vitals: List[Vital] = []
        for match in pattern.finditer(self._raw_text):
            value = _to_decimal(match.group(value_group))
            if value is None:
                continue
            if unit_group is not None:
                raw_unit = match.group(unit_group)
                unit: Optional[str] = raw_unit.strip() if raw_unit else default_unit
            else:
                unit = default_unit
            vitals.append(self._make_vital(document_id, vital_type, value, unit))
        return vitals

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Run regex patterns over ``raw_text`` and return Vital ORM instances.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.

        Args:
            entities: Ignored.  Present for interface compatibility with
                :class:`~app.nlp.base_extractor.BaseNlpExtractor`.
            document_id: UUID of the source Document record.

        Returns:
            list[Vital]: Unsaved ORM instances, one per pattern match.
        """
        vitals: list[Vital] = []

        vitals.extend(self._extract_bp(document_id))
        vitals.extend(self._extract_single(document_id, _HR_PATTERN, "HEART_RATE", default_unit="bpm"))
        vitals.extend(self._extract_single(document_id, _TEMP_PATTERN, "TEMPERATURE", unit_group=2))
        vitals.extend(self._extract_single(document_id, _WEIGHT_PATTERN, "WEIGHT", unit_group=2))
        vitals.extend(self._extract_single(document_id, _HEIGHT_PATTERN, "HEIGHT", unit_group=2))
        vitals.extend(self._extract_single(document_id, _SPO2_PATTERN, "SPO2", default_unit="%"))
        vitals.extend(self._extract_single(document_id, _BMI_PATTERN, "BMI"))

        # Log only count — never log vital values (PHI)
        logger.info(
            "VitalsExtractor complete",
            extra={
                "document_id": str(document_id),
                "vitals_found": len(vitals),
                "confidence": "MEDIUM",
            },
        )

        return vitals
