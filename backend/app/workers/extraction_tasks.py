"""Celery task: extract text from an uploaded PDF document."""
from __future__ import annotations

import asyncio
import uuid

import boto3
from botocore.exceptions import ClientError
from celery.utils.log import get_task_logger

from app.config import settings
from app.extractors.base import ExtractionError
from app.extractors.orchestrator import extract_with_fallback
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def _fetch_pdf_bytes(storage_path: str) -> bytes:
    s3 = _get_s3_client()
    try:
        response = s3.get_object(Bucket=settings.minio_bucket, Key=storage_path)
        return response["Body"].read()
    except ClientError as exc:
        raise ExtractionError(f"MinIO fetch failed for path={storage_path}: {exc}") from exc


async def _run_extraction(document_id: str) -> dict:
    """Core async extraction logic using the document service state machine."""
    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.document import Document  # noqa: PLC0415
    from app.services import document_service  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)

    # Load document — bail out cleanly if deleted
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.document_id == doc_uuid)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.warning("Document not found, skipping", extra={"document_id": document_id})
            return {"document_id": document_id, "status": "NOT_FOUND"}
        storage_path = doc.storage_path

    # Transition to PROCESSING via state machine
    async with AsyncSessionLocal() as session:
        await document_service.mark_processing(session, doc_uuid)

    # Fetch PDF from MinIO (sync boto3)
    pdf_bytes = _fetch_pdf_bytes(storage_path)

    # Get page count for scanned detection (pypdf is already a dependency)
    try:
        import io  # noqa: PLC0415
        from pypdf import PdfReader  # noqa: PLC0415
        reader = PdfReader(io.BytesIO(pdf_bytes))
        page_count = len(reader.pages)
    except Exception:
        page_count = 0

    # Extract via orchestrator (pdfminer → pypdf fallback)
    extraction = extract_with_fallback(pdf_bytes, page_count=page_count)

    # Scanned document: route to MANUAL_REVIEW instead of COMPLETE
    if not extraction.has_text_layer:
        logger.warning(
            "Scanned document detected",
            extra={
                "document_id": document_id,
                "page_count": page_count,
                "char_count": len(extraction.text),
            },
        )
        async with AsyncSessionLocal() as session:
            await document_service.mark_manual_review(
                session, doc_uuid, reason="scanned_document"
            )
        return {
            "document_id": document_id,
            "status": "MANUAL_REVIEW",
            "library_used": extraction.library_used,
            "has_text_layer": False,
        }

    # Persist result and transition to COMPLETE
    async with AsyncSessionLocal() as session:
        await document_service.save_extraction_result(session, doc_uuid, extraction)

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


async def _run_mark_failed(document_id: str, attempts: int) -> None:
    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.services import document_service  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)
    async with AsyncSessionLocal() as session:
        try:
            await document_service.mark_failed(session, doc_uuid, attempts)
        except Exception:
            pass  # Document may have been deleted; safe to ignore


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

    Uses pdfminer.six (primary) with pypdf fallback via ExtractionOrchestrator.
    Status transitions managed by DocumentService state machine.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, library_used, has_text_layer
    """
    logger.info("extract_document started", extra={"document_id": document_id})

    try:
        return asyncio.run(_run_extraction(document_id))
    except ExtractionError as exc:
        attempts = self.request.retries + 1
        asyncio.run(_run_mark_failed(document_id, attempts))
        logger.error(
            "Extraction error",
            extra={"document_id": document_id, "attempt": attempts, "error": str(exc)},
        )
        raise
