"""spaCy + Med7 NLP pipeline: loading and entity extraction."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Med7 labels for medical named entity recognition
MED7_LABELS = frozenset(
    {"DRUG", "DOSAGE", "DURATION", "FORM", "FREQUENCY", "ROUTE", "STRENGTH"}
)

# Module-level singleton — populated on first call to get_nlp()
_nlp = None


def get_nlp():
    """Return the loaded spaCy pipeline, loading it on first call (lazy singleton).

    Attempts to load ``en_core_med7_lg`` (Med7).  If the model is not installed,
    falls back to ``en_core_web_sm`` and logs a warning.  Subsequent calls return
    the same pipeline object without reloading.

    Returns:
        spacy.Language: The loaded pipeline instance.
    """
    global _nlp  # noqa: PLW0603
    if _nlp is not None:
        return _nlp

    import spacy  # noqa: PLC0415

    try:
        _nlp = spacy.load("en_core_med7_lg")
        logger.info("Loaded Med7 pipeline: en_core_med7_lg")
    except OSError:
        logger.warning(
            "Med7 model (en_core_med7_lg) not installed — falling back to en_core_web_sm. "
            "Run 'python -m spacy download en_core_web_sm' or install Med7 for full NLP support."
        )
        _nlp = spacy.load("en_core_web_sm")
        logger.info("Loaded fallback pipeline: en_core_web_sm")

    return _nlp


def extract_entities(text: str) -> list[dict]:
    """Run the NLP pipeline over *text* and return a list of entity dicts.

    Each dict has the shape::

        {
            "text":  str,   # surface form of the entity span
            "label": str,   # entity label, e.g. "DRUG", "DOSAGE"
            "start": int,   # character offset (start, inclusive)
            "end":   int,   # character offset (end, exclusive)
        }

    PHI rule: entity text values are **never** logged — only label counts.

    Args:
        text: Plain text extracted from a medical document.

    Returns:
        list[dict]: Extracted entities, possibly empty if none are found.
    """
    nlp = get_nlp()
    doc = nlp(text)

    entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        }
        for ent in doc.ents
    ]

    # Log only label counts — never log entity text (PHI rule)
    label_counts: dict[str, int] = {}
    for ent in entities:
        label_counts[ent["label"]] = label_counts.get(ent["label"], 0) + 1
    logger.info("Entity extraction complete", extra={"label_counts": label_counts, "total": len(entities)})

    return entities
