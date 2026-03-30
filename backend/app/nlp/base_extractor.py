"""Abstract base class for Med7-label-specific NLP extractors."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List


class BaseNlpExtractor(ABC):
    """Abstract base for extractors that convert Med7 entities into ORM model instances.

    Concrete subclasses handle one Med7 label (e.g. ``DRUG``, ``DOSAGE``) and
    convert the raw entity dicts produced by :func:`app.nlp.pipeline.extract_entities`
    into ORM objects ready for persistence.

    Attributes:
        entity_label: The Med7 label this extractor handles
            (one of ``DRUG``, ``DOSAGE``, ``DURATION``, ``FORM``,
            ``FREQUENCY``, ``ROUTE``, ``STRENGTH``).
    """

    entity_label: str

    @abstractmethod
    def extract(self, entities: List[dict], document_id: uuid.UUID) -> list:
        """Convert relevant entity dicts into ORM model instances.

        Implementations should filter *entities* to those whose ``"label"``
        matches :attr:`entity_label` and return a list of (unsaved) ORM
        instances.  Callers are responsible for persisting the returned objects.

        Args:
            entities: Full list of entity dicts from
                :func:`app.nlp.pipeline.extract_entities`.  Each dict contains
                keys ``text``, ``label``, ``start``, and ``end``.
            document_id: UUID of the source :class:`app.models.document.Document`
                record, used to populate FK relationships on ORM objects.

        Returns:
            list: Unsaved ORM model instances (may be empty).
        """
        ...
