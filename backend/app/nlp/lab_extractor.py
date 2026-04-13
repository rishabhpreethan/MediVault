"""MV-042 (revised): Lab result extractor — tabular + colon-format parser.

Strategy
--------
1. **Tabular parser** — handles whitespace-delimited CBC / haematology reports
   where columns are separated by large runs of spaces::

       Hemoglobin (Hb)         12.5        Low   13.0 - 17.0     g/dL
       Total WBC count         9000              4000-11000       cumm

2. **Colon fallback** — handles narrative reports like "Hemoglobin: 13.5 g/dL".
   Only runs when the tabular parser finds nothing, preventing double-counting.

PHI rule: test names and numeric values are **never** logged — only counts.
"""
from __future__ import annotations

import logging
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from app.models.lab_result import LabResult
from app.nlp.base_extractor import BaseNlpExtractor
from app.nlp.confidence import score_lab

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tabular format (CBC-style)
# Anchor: test-name  <3+ spaces>  numeric-value
# Using [ \t] (not \s) so the pattern never spans newlines.
# ---------------------------------------------------------------------------
_TABULAR_ANCHOR_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9()/. ,\-]{1,79}?)[ \t]{3,}(?P<value>[0-9]+(?:\.[0-9]+)?)",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Colon format (narrative: "Hemoglobin: 13.5 g/dL")
# ---------------------------------------------------------------------------
_COLON_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9()\s/]{1,60}):\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%µ][a-zA-Z0-9/%µ]*)?",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Sub-patterns applied to the tail of a line after the numeric value
# ---------------------------------------------------------------------------
_FLAG_WORD_RE = re.compile(
    r"\b(Low|High|Borderline|Critical|Abnormal|Elevated|Deficient)\b",
    re.IGNORECASE,
)
_REF_RANGE_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*[-\u2013]\s*([0-9]+(?:\.[0-9]+)?)",
)
# Unit must be the last non-whitespace token on the line.
_UNIT_RE = re.compile(
    r"\b([a-zA-Z%µ][a-zA-Z0-9%µ]*(?:/[a-zA-Z0-9µ]+)*)\s*$",
)

# ---------------------------------------------------------------------------
# Noise / section-header detection
# ---------------------------------------------------------------------------
# ALL-CAPS words with 5+ total characters are section headers (HEMOGLOBIN,
# RBC COUNT, …).  Short abbreviations like MCH, MCHC, RDW are kept.
_SECTION_HEADER_RE = re.compile(r"^[A-Z][A-Z\s0-9]{4,}$")

_NOISE_PREFIXES = (
    "primary sample", "sample type", "investigation", "result",
    "reference", "unit", "instrument", "interpretation", "note",
    "generated", "registered", "collected", "reported", "thanks",
    "medical lab", "dr ", "page ", "smart path", "accurate",
    "complete blood", "ref. by", "ref by",
)

_NOISE_EXACT = frozenset({
    "low", "high", "borderline", "critical", "abnormal",
    "elevated", "normal", "calculated", "deficient",
})

# Explicit flag word → standard flag value
_FLAG_MAP: dict[str, str] = {
    "low": "LOW",
    "high": "HIGH",
    "borderline": "HIGH",
    "critical": "CRITICAL",
    "abnormal": "HIGH",
    "elevated": "HIGH",
    "deficient": "LOW",
}

_MIN_TEST_NAME_LEN = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_tail(tail: str) -> Tuple[str, Optional[Decimal], Optional[Decimal], Optional[str]]:
    """Extract flag, reference range, and unit from the text after a value.

    Args:
        tail: Portion of a line that follows the numeric value.

    Returns:
        (flag, ref_low, ref_high, unit) — flag defaults to 'NORMAL'.
    """
    flag = "NORMAL"
    ref_low: Optional[Decimal] = None
    ref_high: Optional[Decimal] = None
    unit: Optional[str] = None

    flag_m = _FLAG_WORD_RE.search(tail)
    if flag_m:
        flag = _FLAG_MAP.get(flag_m.group(1).lower(), "NORMAL")

    ref_m = _REF_RANGE_RE.search(tail)
    if ref_m:
        try:
            ref_low = Decimal(ref_m.group(1))
            ref_high = Decimal(ref_m.group(2))
        except InvalidOperation:
            pass

    unit_m = _UNIT_RE.search(tail)
    if unit_m:
        candidate = unit_m.group(1)
        if candidate.lower() not in _NOISE_EXACT and len(candidate) <= 12:
            unit = candidate

    return flag, ref_low, ref_high, unit


def _infer_flag(
    value: Decimal,
    explicit_flag: str,
    ref_low: Optional[Decimal],
    ref_high: Optional[Decimal],
) -> str:
    """Use explicit flag when present; otherwise infer from reference range."""
    if explicit_flag != "NORMAL":
        return explicit_flag
    if ref_low is not None and ref_high is not None:
        if value < ref_low:
            return "LOW"
        if value > ref_high:
            return "HIGH"
    return "NORMAL"


def _is_noise(name: str) -> bool:
    """Return True when the name string looks like a header, footer, or label."""
    stripped = name.strip()
    if len(stripped) < _MIN_TEST_NAME_LEN:
        return True
    lower = stripped.lower()
    if lower in _NOISE_EXACT:
        return True
    if any(lower.startswith(p) for p in _NOISE_PREFIXES):
        return True
    if _SECTION_HEADER_RE.match(stripped):
        return True
    return False


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class LabExtractor(BaseNlpExtractor):
    """Extract lab results from raw report text.

    Args:
        member_id: UUID of the owning FamilyMember record.
        raw_text:  Plain-text content extracted from the document.
    """

    entity_label: str = "LAB"

    def __init__(self, member_id: uuid.UUID, raw_text: str) -> None:
        self._member_id = member_id
        self._raw_text = raw_text

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Return LabResult ORM instances parsed from raw_text.

        The ``entities`` parameter is accepted for interface compatibility but
        is not used — this extractor operates on raw text only.
        """
        results = self._extract_tabular(document_id)
        if not results:
            # Tabular found nothing — try colon-format as fallback
            results = self._extract_colon(document_id)

        logger.info(
            "LabExtractor complete",
            extra={"document_id": str(document_id), "labs_found": len(results)},
        )
        return results

    # ------------------------------------------------------------------
    # Tabular parser
    # ------------------------------------------------------------------

    def _extract_tabular(self, document_id: uuid.UUID) -> list[LabResult]:
        text = self._raw_text
        results: list[LabResult] = []

        for m in _TABULAR_ANCHOR_RE.finditer(text):
            name = m.group("name").strip()
            value_str = m.group("value")

            if _is_noise(name):
                continue

            try:
                value = Decimal(value_str)
            except InvalidOperation:
                continue

            # Slice the rest of the line (from after the value to the newline)
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            tail = text[m.end():line_end]

            flag, ref_low, ref_high, unit = _parse_tail(tail)
            flag = _infer_flag(value, flag, ref_low, ref_high)
            confidence = score_lab(value_found=True, unit_found=unit is not None).value

            results.append(LabResult(
                member_id=self._member_id,
                document_id=document_id,
                test_name=name,
                value=value,
                value_text=value_str,
                unit=unit,
                reference_low=ref_low,
                reference_high=ref_high,
                flag=flag,
                confidence_score=confidence,
                is_manual_entry=False,
            ))

        return results

    # ------------------------------------------------------------------
    # Colon-format fallback
    # ------------------------------------------------------------------

    def _extract_colon(self, document_id: uuid.UUID) -> list[LabResult]:
        results: list[LabResult] = []

        for m in _COLON_RE.finditer(self._raw_text):
            name = m.group(1).strip()
            value_str = m.group(2).strip()
            unit_raw = m.group(3)
            unit = unit_raw.strip() if unit_raw else None

            if _is_noise(name):
                continue

            try:
                value = Decimal(value_str)
            except InvalidOperation:
                continue

            confidence = score_lab(value_found=True, unit_found=unit is not None).value

            results.append(LabResult(
                member_id=self._member_id,
                document_id=document_id,
                test_name=name,
                value=value,
                value_text=value_str,
                unit=unit,
                flag="NORMAL",
                confidence_score=confidence,
                is_manual_entry=False,
            ))

        return results
