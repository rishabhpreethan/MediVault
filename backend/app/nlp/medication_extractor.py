"""MV-041: Medication extractor — groups DRUG entities with nearby Med7 attributes."""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.nlp.base_extractor import BaseNlpExtractor
from app.models.medication import Medication

logger = logging.getLogger(__name__)

# Character window on each side of a DRUG entity to search for related attributes
_WINDOW = 200

# Med7 attribute labels that can be linked to a DRUG entity
_ATTRIBUTE_LABELS = frozenset({"DOSAGE", "FREQUENCY", "DURATION", "ROUTE", "FORM", "STRENGTH"})


class MedicationExtractor(BaseNlpExtractor):
    """Extract medications from Med7 entities and group nearby attributes.

    For each ``DRUG`` entity, scans within a ``±200`` character window for
    ``DOSAGE``, ``FREQUENCY``, ``DURATION``, ``ROUTE``, ``FORM``, and
    ``STRENGTH`` entities and bundles them into a :class:`Medication` ORM
    instance.

    Confidence rules:
    - ``HIGH`` — drug + at least one DOSAGE found
    - ``MEDIUM`` — drug found without DOSAGE
    - ``LOW``  — (unused; kept for symmetry with other extractors)

    PHI rule: entity *text* is **never** logged — only counts and confidence
    level distributions, plus ``document_id``.

    Args:
        member_id: UUID of the owning ``FamilyMember`` record.  Required for
            persisting ORM instances.
    """

    entity_label: str = "DRUG"

    def __init__(self, member_id: uuid.UUID) -> None:
        self._member_id = member_id

    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Convert DRUG entities (with nearby attributes) into Medication ORM instances.

        Args:
            entities: Full entity list from
                :func:`app.nlp.pipeline.extract_entities`.
            document_id: UUID of the source Document record.

        Returns:
            list[Medication]: Unsaved ORM instances, one per DRUG entity.
        """
        drugs = [e for e in entities if e["label"] == "DRUG"]
        attributes = [e for e in entities if e["label"] in _ATTRIBUTE_LABELS]

        medications: list[Medication] = []

        for drug in drugs:
            drug_start: int = drug["start"]
            drug_end: int = drug["end"]
            window_start = max(0, drug_start - _WINDOW)
            window_end = drug_end + _WINDOW

            # Collect nearby attribute entities by label
            nearby: dict[str, str] = {}
            for attr in attributes:
                attr_mid = (attr["start"] + attr["end"]) / 2
                if window_start <= attr_mid <= window_end:
                    label = attr["label"]
                    # Keep the first match per label (closest proximity not tracked yet)
                    if label not in nearby:
                        nearby[label] = attr["text"]

            # Confidence: HIGH if dosage found, MEDIUM if drug-only
            has_dosage = "DOSAGE" in nearby
            confidence = "HIGH" if has_dosage else "MEDIUM"

            med = Medication(
                member_id=self._member_id,
                document_id=document_id,
                drug_name=drug["text"],
                dosage=nearby.get("DOSAGE"),
                frequency=nearby.get("FREQUENCY"),
                route=nearby.get("ROUTE"),
                confidence_score=confidence,
                is_manual_entry=False,
            )
            medications.append(med)

        # Log only counts and confidence distribution — never log drug names (PHI)
        confidence_dist: dict[str, int] = {}
        for m in medications:
            confidence_dist[m.confidence_score] = confidence_dist.get(m.confidence_score, 0) + 1

        logger.info(
            "MedicationExtractor complete",
            extra={
                "document_id": str(document_id),
                "medications_found": len(medications),
                "confidence_distribution": confidence_dist,
            },
        )

        return medications
