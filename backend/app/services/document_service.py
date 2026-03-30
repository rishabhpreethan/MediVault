"""Document service — state machine for processing_status transitions and
raw-text persistence.

Status state machine:
  QUEUED → PROCESSING
  PROCESSING → COMPLETE
  PROCESSING → FAILED
  FAILED → PROCESSING        (on manual retry)
  FAILED → MANUAL_REVIEW     (after max attempts exceeded)
  MANUAL_REVIEW → PROCESSING (on manual retry — operator override)
  COMPLETE → PROCESSING      (on manual retry — re-extract)

All other transitions are invalid and raise InvalidStatusTransition.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.extractors.base import ExtractionResult

# ---------------------------------------------------------------------------
# Status constants (mirror the DB enum values)
# ---------------------------------------------------------------------------
QUEUED = "QUEUED"
PROCESSING = "PROCESSING"
COMPLETE = "COMPLETE"
FAILED = "FAILED"
MANUAL_REVIEW = "MANUAL_REVIEW"

MAX_AUTO_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# Allowed transitions:  from_status → {allowed to_statuses}
# ---------------------------------------------------------------------------
_ALLOWED: dict[str, set[str]] = {
    QUEUED: {PROCESSING},
    PROCESSING: {COMPLETE, FAILED},
    FAILED: {PROCESSING, MANUAL_REVIEW},
    MANUAL_REVIEW: {PROCESSING},
    COMPLETE: {PROCESSING},
}


class InvalidStatusTransition(Exception):
    """Raised when a status transition is not permitted."""


def assert_valid_transition(from_status: str, to_status: str) -> None:
    """Raise InvalidStatusTransition if the transition is not allowed."""
    allowed = _ALLOWED.get(from_status, set())
    if to_status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition document from {from_status!r} to {to_status!r}. "
            f"Allowed: {sorted(allowed)}"
        )


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def mark_processing(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Transition document to PROCESSING and increment extraction_attempts."""
    from app.models.document import Document  # noqa: PLC0415

    doc = await _get_or_raise(session, document_id)
    assert_valid_transition(doc.processing_status, PROCESSING)
    doc.processing_status = PROCESSING
    doc.extraction_attempts = (doc.extraction_attempts or 0) + 1
    await session.commit()


async def save_extraction_result(
    session: AsyncSession,
    document_id: uuid.UUID,
    result: ExtractionResult,
) -> None:
    """Persist extracted text and transition document to COMPLETE."""
    from app.models.document import Document  # noqa: PLC0415

    doc = await _get_or_raise(session, document_id)
    assert_valid_transition(doc.processing_status, COMPLETE)
    doc.extracted_raw_text = result.text
    doc.has_text_layer = result.has_text_layer
    doc.extraction_library = result.library_used
    doc.processing_status = COMPLETE
    doc.processed_at = datetime.now(tz=timezone.utc)
    await session.commit()


async def mark_failed(
    session: AsyncSession,
    document_id: uuid.UUID,
    attempts: int,
) -> None:
    """Transition document to FAILED or MANUAL_REVIEW based on attempt count."""
    from app.models.document import Document  # noqa: PLC0415

    doc = await _get_or_raise(session, document_id)
    to_status = MANUAL_REVIEW if attempts >= MAX_AUTO_ATTEMPTS else FAILED
    assert_valid_transition(doc.processing_status, to_status)
    doc.processing_status = to_status
    await session.commit()


async def mark_queued_for_retry(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> None:
    """Reset a FAILED or MANUAL_REVIEW document back to QUEUED for retry.

    Called by the manual retry API endpoint (MV-021 / MV-027).
    """
    from app.models.document import Document  # noqa: PLC0415

    doc = await _get_or_raise(session, document_id)
    # Retry resets to PROCESSING directly (task will be re-queued by caller)
    assert_valid_transition(doc.processing_status, PROCESSING)
    doc.processing_status = PROCESSING
    doc.extraction_attempts = (doc.extraction_attempts or 0) + 1
    await session.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_or_raise(session: AsyncSession, document_id: uuid.UUID):
    from app.models.document import Document  # noqa: PLC0415

    result = await session.execute(
        select(Document).where(Document.document_id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise ValueError(f"Document {document_id} not found")
    return doc
