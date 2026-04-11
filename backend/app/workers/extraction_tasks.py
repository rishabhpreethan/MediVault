"""Celery task: extract text from an uploaded PDF document."""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

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


def _make_async_session_factory():
    """Create a fresh async engine + session factory bound to the current event loop.

    Must be called *inside* an asyncio.run() so the engine is bound to the
    correct loop. The module-level engine (database.py) is attached to the
    FastAPI loop and cannot be reused inside Celery's asyncio.run() calls.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: PLC0415
    _engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=2, max_overflow=0)
    return async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _run_extraction(document_id: str) -> dict:
    """Core async extraction logic using the document service state machine."""
    AsyncSessionLocal = _make_async_session_factory()
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
        member_id = doc.member_id
        document_type = doc.document_type
        user_id = doc.user_id

    # Fetch the user's email for notifications (best-effort; None is safe)
    user_email: Optional[str] = None
    try:
        from app.models.user import User  # noqa: PLC0415
        async with AsyncSessionLocal() as session:
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user is not None:
                user_email = user.email
    except Exception:
        pass  # Notifications are best-effort; never block extraction

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

    # Send notification (no-op if disabled or key not set)
    _notify_processing_complete(document_type, user_email)

    logger.info(
        "Extraction complete",
        extra={
            "document_id": document_id,
            "library": extraction.library_used,
            "has_text_layer": extraction.has_text_layer,
            "char_count": len(extraction.text),
        },
    )

    # Run entity deduplication for the member whose document was just processed.
    # member_id is read from the document loaded earlier in this function.
    async with AsyncSessionLocal() as session:
        from app.services.deduplication_service import run_deduplication  # noqa: PLC0415
        dedup_counts = await run_deduplication(session, member_id)
        logger.info(
            "Deduplication complete",
            extra={"document_id": document_id, **dedup_counts},
        )

    # Chain to NLP task to extract structured entities from the raw text
    from app.workers.nlp_tasks import process_nlp  # noqa: PLC0415
    process_nlp.apply_async(args=[document_id], queue="nlp")

    return {
        "document_id": document_id,
        "status": "COMPLETE",
        "library_used": extraction.library_used,
        "has_text_layer": extraction.has_text_layer,
    }


async def _run_mark_failed(document_id: str, attempts: int) -> Optional[dict]:
    """Mark a document as failed and return metadata needed for notifications."""
    AsyncSessionLocal = _make_async_session_factory()
    from app.models.document import Document  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415
    from app.services import document_service  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    doc_uuid = uuid.UUID(document_id)

    document_type: Optional[str] = None
    user_email: Optional[str] = None

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Document).where(Document.document_id == doc_uuid)
            )
            doc = result.scalar_one_or_none()
            if doc is not None:
                document_type = doc.document_type
                user_id = doc.user_id
                user_result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                if user is not None:
                    user_email = user.email
    except Exception:
        pass  # Best-effort; don't block the failed-mark

    async with AsyncSessionLocal() as session:
        try:
            await document_service.mark_failed(session, doc_uuid, attempts)
        except Exception:
            pass  # Document may have been deleted; safe to ignore

    return {"document_type": document_type, "user_email": user_email}


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
        failed_meta = asyncio.run(_run_mark_failed(document_id, attempts))
        logger.error(
            "Extraction error",
            extra={"document_id": document_id, "attempt": attempts, "error": str(exc)},
        )
        if failed_meta:
            _notify_extraction_failed(
                failed_meta.get("document_type"),
                failed_meta.get("user_email"),
            )
        raise


# ---------------------------------------------------------------------------
# Notification helpers — best-effort; never raise
# ---------------------------------------------------------------------------

def _notify_processing_complete(
    document_type: Optional[str],
    user_email: Optional[str],
) -> None:
    """Send a processing-complete email. No-op if email or type is missing."""
    if not user_email or not document_type:
        return
    try:
        from app.services.email_service import send_processing_complete_email  # noqa: PLC0415
        send_processing_complete_email(
            to=user_email,
            document_type=document_type,
            app_url=settings.cors_origins[0] if settings.cors_origins else "https://medivault.health",
        )
    except Exception:
        pass  # Notification failure must never affect extraction result


def _notify_extraction_failed(
    document_type: Optional[str],
    user_email: Optional[str],
) -> None:
    """Send an extraction-failed email. No-op if email or type is missing."""
    if not user_email or not document_type:
        return
    try:
        from app.services.email_service import send_extraction_failed_email  # noqa: PLC0415
        send_extraction_failed_email(
            to=user_email,
            document_type=document_type,
            app_url=settings.cors_origins[0] if settings.cors_origins else "https://medivault.health",
        )
    except Exception:
        pass  # Notification failure must never affect extraction result
