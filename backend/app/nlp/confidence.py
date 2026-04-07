"""MV-047: Confidence scoring utilities for NLP extraction results."""
from __future__ import annotations

from enum import Enum
from typing import Optional


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted clinical entities."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def score_medication(
    drug_found: bool,
    dosage_found: bool,
    frequency_found: bool,  # noqa: ARG001 — reserved for future scoring refinements
) -> ConfidenceLevel:
    """Score confidence for an extracted medication.

    Rules:
    - HIGH   — drug name AND dosage both found
    - MEDIUM — drug name found, dosage absent
    - LOW    — drug name not found

    Args:
        drug_found: Whether a drug entity was identified.
        dosage_found: Whether a dosage entity was linked to the drug.
        frequency_found: Whether a frequency entity was linked (reserved for
            future refinement; does not affect current scoring).

    Returns:
        ConfidenceLevel for the medication extraction.
    """
    if drug_found and dosage_found:
        return ConfidenceLevel.HIGH
    if drug_found:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def score_lab(
    value_found: bool,
    unit_found: bool,
) -> ConfidenceLevel:
    """Score confidence for an extracted lab result.

    Rules:
    - HIGH   — numeric value AND unit both found
    - MEDIUM — numeric value found, unit absent
    - LOW    — no numeric value found

    Args:
        value_found: Whether a numeric value was extracted.
        unit_found: Whether a unit string was extracted.

    Returns:
        ConfidenceLevel for the lab result extraction.
    """
    if value_found and unit_found:
        return ConfidenceLevel.HIGH
    if value_found:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def score_diagnosis(trigger_type: str) -> ConfidenceLevel:
    """Score confidence for an extracted diagnosis based on trigger keyword.

    Rules:
    - MEDIUM — trigger is "diagnosed with" (explicit statement)
    - LOW    — trigger is an impression/assessment/diagnosis header (inferred)

    Args:
        trigger_type: The matched trigger string.  Expected values are
            ``"diagnosed with"``, ``"impression"``, ``"assessment"``,
            ``"diagnosis"``, or any other keyword found by the extractor.

    Returns:
        ConfidenceLevel for the diagnosis extraction.
    """
    if trigger_type.lower().strip() == "diagnosed with":
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def flag_low_confidence(
    items: list,
    confidence_field: str = "confidence_score",
) -> list[dict]:
    """Annotate a list of extracted items with a ``needs_review`` flag.

    Each item whose ``confidence_field`` attribute equals
    :attr:`ConfidenceLevel.LOW` is marked ``needs_review=True``.

    Args:
        items: Sequence of objects (ORM instances or dicts) that carry a
            confidence value.  Attribute access is tried first; dict key
            access is used as a fallback.
        confidence_field: Name of the attribute / key that holds the
            confidence value.  Defaults to ``"confidence_score"``.

    Returns:
        list[dict] where each dict has keys ``item`` (the original object)
        and ``needs_review`` (bool).
    """
    results: list[dict] = []
    for item in items:
        # Support both ORM instances (attribute access) and plain dicts
        if isinstance(item, dict):
            value: Optional[str] = item.get(confidence_field)
        else:
            value = getattr(item, confidence_field, None)

        needs_review = value == ConfidenceLevel.LOW or value == ConfidenceLevel.LOW.value
        results.append({"item": item, "needs_review": needs_review})
    return results
