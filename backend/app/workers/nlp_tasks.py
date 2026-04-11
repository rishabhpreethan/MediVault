"""Celery task: run NLP entity extraction on a document's raw text."""
from __future__ import annotations

import asyncio
import uuid

from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def _make_async_session_factory():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: PLC0415
    from app.config import settings  # noqa: PLC0415
    _engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=2, max_overflow=0)
    return async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _run_nlp(document_id: str) -> dict:
    """Core async NLP logic: fetch raw text from DB, extract entities, persist results.

    PHI rule: entity text, test names, drug names, and condition names are
    **never** logged — only counts, confidence distributions, and document_id.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, medications_found, labs_found,
        diagnoses_found
    """
    AsyncSessionLocal = _make_async_session_factory()
    from app.models.document import Document  # noqa: PLC0415
    from app.nlp.pipeline import extract_entities  # noqa: PLC0415
    from app.nlp.medication_extractor import MedicationExtractor  # noqa: PLC0415
    from app.nlp.lab_extractor import LabExtractor  # noqa: PLC0415
    from app.nlp.diagnosis_extractor import DiagnosisExtractor  # noqa: PLC0415
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

    member_id: uuid.UUID = doc.member_id

    # Step 1: Run Med7 NLP pipeline — extract_entities logs label counts (no PHI)
    entities = extract_entities(raw_text)

    # Step 2: Instantiate extractors
    medication_extractor = MedicationExtractor(member_id=member_id)
    lab_extractor = LabExtractor(member_id=member_id, raw_text=raw_text)
    diagnosis_extractor = DiagnosisExtractor(member_id=member_id, raw_text=raw_text)

    # Step 3: Run each extractor
    medications = medication_extractor.extract(entities, doc_uuid)
    labs = lab_extractor.extract(entities, doc_uuid)
    diagnoses = diagnosis_extractor.extract(entities, doc_uuid)

    # Step 4: Persist all results in a single async session
    AsyncSessionLocal = _make_async_session_factory()
    async with AsyncSessionLocal() as session:
        session.add_all(medications)
        session.add_all(labs)
        session.add_all(diagnoses)
        await session.commit()

    # Step 5: Log only counts — never log entity values (PHI)
    logger.info(
        "NLP extraction and persistence complete",
        extra={
            "document_id": document_id,
            "medications_found": len(medications),
            "labs_found": len(labs),
            "diagnoses_found": len(diagnoses),
        },
    )

    return {
        "document_id": document_id,
        "status": "COMPLETE",
        "medications_found": len(medications),
        "labs_found": len(labs),
        "diagnoses_found": len(diagnoses),
    }


@celery_app.task(
    bind=True,
    name="nlp.process_nlp",
    queue="nlp",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_nlp(self, document_id: str) -> dict:
    """Run NLP entity extraction on a document's extracted raw text.

    Fetches the document's ``extracted_raw_text`` from the database, runs the
    spaCy/Med7 pipeline, extracts medications, lab results, and diagnoses, and
    persists them all in a single database session.

    PHI rule: entity text is **never** logged — only counts and document_id.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, medications_found, labs_found,
        diagnoses_found
    """
    logger.info("process_nlp started", extra={"document_id": document_id})
    return asyncio.run(_run_nlp(document_id))
