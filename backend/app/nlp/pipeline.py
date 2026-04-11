"""spaCy NLP pipeline: loading and entity extraction.

Uses scispaCy (en_ner_bc5cdr_md) for medical NER when available,
falling back to en_core_web_sm. scispaCy provides CHEMICAL (drug names)
and DISEASE labels. DOSAGE / FREQUENCY / ROUTE / DURATION labels are
emitted by the companion regex helpers so downstream extractors remain
unchanged.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Labels produced by this module (union of scispaCy + regex helpers)
MED7_LABELS = frozenset(
    {"DRUG", "DOSAGE", "DURATION", "FORM", "FREQUENCY", "ROUTE", "STRENGTH"}
)

# ---------------------------------------------------------------------------
# Regex helpers for attributes Med7 / scispaCy do not emit
# ---------------------------------------------------------------------------

_DOSAGE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|µg|g|ml|mL|IU|units?|mmol|mEq)"
    r"(?:/\s*\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|mL))?",
    re.IGNORECASE,
)
_FREQUENCY_RE = re.compile(
    r"\b(?:once|twice|thrice|three\s+times|four\s+times)\s+(?:a\s+)?(?:daily|day|week|month)"
    r"|\b(?:OD|BD|BID|TID|QID|QDS|TDS|SOS|PRN|HS|AC|PC|STAT)\b"
    r"|\bevery\s+\d+\s+hours?"
    r"|\b(?:daily|weekly|monthly|nightly|nocte)\b",
    re.IGNORECASE,
)
_ROUTE_RE = re.compile(
    r"\b(?:oral(?:ly)?|PO|IV|IM|SC|SL|sublingual|topical(?:ly)?|"
    r"inhal(?:ed|ation)|intranasal|rectal(?:ly)?|transdermal)\b",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(
    r"\b(?:for\s+|x\s*)?\d+\s*(?:days?|weeks?|months?|hours?)\b",
    re.IGNORECASE,
)
_FORM_RE = re.compile(
    r"\b(?:tablet|capsule|cap|tab|syrup|suspension|injection|cream|ointment|"
    r"gel|drops?|inhaler|spray|patch|suppository|solution|lotion)\b",
    re.IGNORECASE,
)

# Module-level singleton
_nlp = None


def get_nlp():
    """Return the loaded spaCy pipeline (lazy singleton).

    Preference order:
      1. en_core_sci_sm (scispaCy — lightweight, installs cleanly)
      2. en_ner_bc5cdr_md  (scispaCy — CHEMICAL + DISEASE; larger)
      3. en_core_web_sm    (last resort; no medical entities)
    """
    global _nlp  # noqa: PLW0603
    if _nlp is not None:
        return _nlp

    import spacy  # noqa: PLC0415

    for model_name in ("en_ner_bc5cdr_md", "en_core_sci_sm", "en_core_web_sm"):
        try:
            _nlp = spacy.load(model_name)
            logger.info("Loaded NLP pipeline: %s", model_name)
            return _nlp
        except OSError:
            continue

    raise RuntimeError(
        "No spaCy model available. Run: python -m spacy download en_core_web_sm"
    )


def extract_entities(text: str) -> list[dict]:
    """Run the NLP pipeline over *text* and return a list of entity dicts.

    scispaCy's CHEMICAL label is remapped to DRUG so that MedicationExtractor
    works without changes. DISEASE is kept as-is (DiagnosisExtractor uses its
    own regex and ignores entities, but future callers may use it).

    Additional DOSAGE / FREQUENCY / ROUTE / DURATION / FORM entities are
    produced by lightweight regex so MedicationExtractor can group attributes
    around each DRUG entity.

    PHI rule: entity text values are **never** logged — only label counts.
    """
    nlp = get_nlp()
    doc = nlp(text)

    # Remap scispaCy labels to Med7-compatible labels
    _label_map = {"CHEMICAL": "DRUG", "DISEASE": "DIAGNOSIS"}

    entities: list[dict] = [
        {
            "text": ent.text,
            "label": _label_map.get(ent.label_, ent.label_),
            "start": ent.start_char,
            "end": ent.end_char,
        }
        for ent in doc.ents
    ]

    # Supplement with regex-based attribute entities
    regex_rules: list[tuple[re.Pattern, str]] = [
        (_DOSAGE_RE, "DOSAGE"),
        (_FREQUENCY_RE, "FREQUENCY"),
        (_ROUTE_RE, "ROUTE"),
        (_DURATION_RE, "DURATION"),
        (_FORM_RE, "FORM"),
    ]
    for pattern, label in regex_rules:
        for m in pattern.finditer(text):
            entities.append({
                "text": m.group(),
                "label": label,
                "start": m.start(),
                "end": m.end(),
            })

    # Log only label counts — never log entity text (PHI rule)
    label_counts: dict[str, int] = {}
    for ent in entities:
        label_counts[ent["label"]] = label_counts.get(ent["label"], 0) + 1
    logger.info(
        "Entity extraction complete",
        extra={"label_counts": label_counts, "total": len(entities)},
    )

    return entities
