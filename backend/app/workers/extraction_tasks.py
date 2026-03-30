"""Celery task: extract text from an uploaded PDF document."""
import asyncio
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.extractors.base import ExtractionError
from app.extractors.pdfminer_extractor import PdfminerExtractor
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)

# Status constants — mirror the DB enum
_PROCESSING = "PROCESSING"
_COMPLETE = "COMPLETE"
_FAILED = "FAILED"
_MANUAL_REVIEW = "MANUAL_REVIEW"


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


async def _fetch_pdf_bytes(storage_path: str) -> bytes:
    """Fetch PDF bytes from MinIO. Runs in async context via asyncio.run()."""
    s3 = _get_s3_client()
    try:
        response = s3.get_object(Bucket=settings.minio_bucket, Key=storage_path)
        return response["Body"].read()
    except ClientError as exc:
        raise ExtractionError(f"MinIO fetch failed for path={storage_path}: {exc}") from exc


async def _run_extraction(document_id: str) -> dict:
    """Core async extraction logic — loads doc, fetches PDF, extracts, saves result."""
    # Import here to avoid circular imports at module load time
    from app.models.document import Document  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.document_id == doc_uuid)
        )
        doc = result.scalar_one_or_none()

        if doc is None:
            # Document was deleted — do not retry
            logger.warning("Document not found, skipping", extra={"document_id": document_id})
            return {"document_id": document_id, "status": "NOT_FOUND"}

        # Mark as processing
        doc.processing_status = _PROCESSING
        doc.extraction_attempts = (doc.extraction_attempts or 0) + 1
        await session.commit()

    # Fetch PDF bytes from MinIO (outside session to avoid long-held connections)
    pdf_bytes = await _fetch_pdf_bytes(doc.storage_path)

    # Extract — synchronous pdfminer call
    extractor = PdfminerExtractor()
    extraction = extractor.extract(pdf_bytes)

    # Persist results
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.document_id == doc_uuid)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return {"document_id": document_id, "status": "NOT_FOUND"}

        doc.extracted_raw_text = extraction.text
        doc.has_text_layer = extraction.has_text_layer
        doc.extraction_library = extraction.library_used
        doc.processing_status = _COMPLETE
        doc.processed_at = datetime.now(tz=timezone.utc)
        await session.commit()

    logger.info(
        "Extraction complete",
        extra={
            "document_id": document_id,
            "library": extraction.library_used,
            "has_text_layer": extraction.has_text_layer,
            "char_count": len(extraction.text),
        },
    )
    return {
        "document_id": document_id,
        "status": "COMPLETE",
        "library_used": extraction.library_used,
        "has_text_layer": extraction.has_text_layer,
    }


async def _mark_failed(document_id: str, attempts: int) -> None:
    from app.models.document import Document  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)
    status = _MANUAL_REVIEW if attempts >= 3 else _FAILED

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.document_id == doc_uuid)
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.processing_status = status
            await session.commit()

    logger.error(
        "Extraction failed",
        extra={"document_id": document_id, "attempts": attempts, "final_status": status},
    )


@celery_app.task(
    bind=True,
    name="extraction.extract_document",
    queue="extraction",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ExtractionError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def extract_document(self, document_id: str) -> dict:
    """Extract text from a PDF document stored in MinIO.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, library_used, has_text_layer
    """
    logger.info("extract_document started", extra={"document_id": document_id})

    try:
        result = asyncio.run(_run_extraction(document_id))
        return result
    except ExtractionError as exc:
        attempts = self.request.retries + 1
        asyncio.run(_mark_failed(document_id, attempts))
        logger.error(
            "Extraction error",
            extra={"document_id": document_id, "attempt": attempts, "error": str(exc)},
        )
        raise
