"""Celery task: run NLP entity extraction on a document's raw text."""
from __future__ import annotations

import asyncio
import uuid

from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


async def _run_nlp(document_id: str) -> dict:
    """Core async NLP logic: fetch raw text from DB and extract entities.

    PHI rule: entity text is **never** logged — only label counts and IDs.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, label_counts, total_entities
    """
    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.document import Document  # noqa: PLC0415
    from app.nlp.pipeline import extract_entities  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.document_id == doc_uuid)
        )
        doc = result.scalar_one_or_none()

    if doc is None:
        logger.warning("Document not found, skipping NLP", extra={"document_id": document_id})
        return {"document_id": document_id, "status": "NOT_FOUND"}

    raw_text: str = doc.extracted_raw_text or ""
    if not raw_text.strip():
        logger.warning(
            "Document has no extracted text, skipping NLP",
            extra={"document_id": document_id},
        )
        return {"document_id": document_id, "status": "NO_TEXT"}

    # Run NLP — extract_entities logs label counts internally (no PHI)
    entities = extract_entities(raw_text)

    # Aggregate label counts for the return summary (no entity text logged here)
    label_counts: dict[str, int] = {}
    for ent in entities:
        label_counts[ent["label"]] = label_counts.get(ent["label"], 0) + 1

    logger.info(
        "NLP extraction complete",
        extra={
            "document_id": document_id,
            "total_entities": len(entities),
            "label_counts": label_counts,
        },
    )

    # Entity persistence is handled in MV-041+
    return {
        "document_id": document_id,
        "status": "COMPLETE",
        "total_entities": len(entities),
        "label_counts": label_counts,
    }


@celery_app.task(
    bind=True,
    name="nlp.process_document",
    queue="nlp",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_document(self, document_id: str) -> dict:
    """Run NLP entity extraction on a document's extracted raw text.

    Fetches the document's ``extracted_raw_text`` from the database, runs the
    spaCy/Med7 pipeline via :func:`app.nlp.pipeline.extract_entities`, and
    returns a summary.  Actual entity persistence is implemented in MV-041+.

    PHI rule: entity text is **never** logged — only counts, labels, and IDs.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, total_entities, label_counts
    """
    logger.info("process_document started", extra={"document_id": document_id})
    return asyncio.run(_run_nlp(document_id))
