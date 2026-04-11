"""Documents API — upload, list, retrieve, and delete medical PDF documents."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select

from app.limiter import limiter

from app.dependencies import CurrentUser, DbSession, require_member_access
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.document import Document
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.schemas.documents import DocumentListResponse, DocumentResponse, DocumentStatusResponse
from app.schemas.entity_crud import (
    AllergyResponse,
    DiagnosisResponse,
    LabResultResponse,
    MedicationResponse,
)
from app.services import document_service
from app.services.storage_service import delete_file, upload_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_VALID_DOCUMENT_TYPES = {"LAB_REPORT", "PRESCRIPTION", "DISCHARGE_SUMMARY", "OTHER"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_member_or_404(
    db: DbSession,
    member_id: uuid.UUID,
    current_user,
) -> FamilyMember:
    """Load a FamilyMember and verify ownership, or raise 404 / 403."""
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == member_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )
    # Confirm the member belongs to the current user.
    require_member_access(member.user_id, current_user)
    return member


async def _load_document_or_404(
    db: DbSession,
    document_id: uuid.UUID,
    current_user,
) -> Document:
    """Load a Document and verify ownership via its member, or raise 404 / 403."""
    result = await db.execute(
        select(Document).where(Document.document_id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    # Ownership is tracked directly on the document row as well.
    if doc.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return doc


def _document_to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        document_id=str(doc.document_id),
        member_id=str(doc.member_id),
        document_type=doc.document_type,
        document_date=doc.document_date,
        original_filename=doc.original_filename or "",
        file_size_bytes=doc.file_size_bytes or 0,
        processing_status=doc.processing_status,
        has_text_layer=doc.has_text_layer,
        extraction_library=doc.extraction_library,
        uploaded_at=doc.uploaded_at,
        processed_at=doc.processed_at,
    )


# ---------------------------------------------------------------------------
# POST /documents/upload
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile,
    member_id: uuid.UUID = Form(...),
    document_type: str = Form(...),
    document_date: Optional[str] = Form(None),
) -> DocumentResponse:
    """Upload a PDF document for a family member.

    Validates content-type, file size, and member ownership before storing the
    file in MinIO and queuing an extraction task.
    """
    # -- Validate document_type -----------------------------------------------
    if document_type not in _VALID_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid document_type. Allowed values: {sorted(_VALID_DOCUMENT_TYPES)}",
        )

    # -- Validate content-type ------------------------------------------------
    content_type = (file.content_type or "").lower()
    filename = file.filename or ""
    if content_type not in _ALLOWED_CONTENT_TYPES or not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted (content-type: application/pdf, .pdf extension)",
        )

    # -- Read file bytes and enforce size limit --------------------------------
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {_MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    # -- Parse optional document_date -----------------------------------------
    parsed_date = None
    if document_date:
        from datetime import date as date_type  # noqa: PLC0415

        try:
            parsed_date = date_type.fromisoformat(document_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="document_date must be in ISO 8601 format (YYYY-MM-DD)",
            )

    # -- Verify member ownership ----------------------------------------------
    await _load_member_or_404(db, member_id, current_user)

    # -- Build document record ------------------------------------------------
    document_id = uuid.uuid4()
    storage_path = f"{current_user.user_id}/{member_id}/{document_id}.pdf"

    doc = Document(
        document_id=document_id,
        member_id=member_id,
        user_id=current_user.user_id,
        document_type=document_type,
        document_date=parsed_date,
        original_filename=filename,
        storage_path=storage_path,
        file_size_bytes=len(pdf_bytes),
        processing_status=document_service.QUEUED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # -- Upload to MinIO (sync boto3 call, acceptable in handler for now) ------
    try:
        upload_pdf(pdf_bytes, storage_path)
    except Exception as exc:
        # Roll back the DB record if storage fails so we don't leave orphans.
        await db.delete(doc)
        await db.commit()
        logger.error(
            "MinIO upload failed; DB record rolled back",
            extra={"document_id": str(document_id), "member_id": str(member_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable — please retry",
        ) from exc

    # -- Dispatch extraction task ---------------------------------------------
    from app.workers.extraction_tasks import extract_document  # noqa: PLC0415

    extract_document.apply_async(args=[str(document_id)], queue="extraction")

    logger.info(
        "Document uploaded and queued",
        extra={
            "document_id": str(document_id),
            "member_id": str(member_id),
            "file_size_bytes": len(pdf_bytes),
        },
    )

    return _document_to_response(doc)


# ---------------------------------------------------------------------------
# GET /documents/
# ---------------------------------------------------------------------------


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    member_id: uuid.UUID = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DocumentListResponse:
    """Return a paginated list of documents for a family member."""
    await _load_member_or_404(db, member_id, current_user)

    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).where(Document.member_id == member_id)
    )
    total = total_result.scalar_one()

    docs_result = await db.execute(
        select(Document)
        .where(Document.member_id == member_id)
        .order_by(Document.uploaded_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    docs = docs_result.scalars().all()

    return DocumentListResponse(
        items=[_document_to_response(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /documents/{document_id}
# ---------------------------------------------------------------------------


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentResponse:
    """Return a single document by ID with all extracted entities."""
    doc = await _load_document_or_404(db, document_id, current_user)
    base = _document_to_response(doc)

    meds_r = await db.execute(select(Medication).where(Medication.document_id == document_id))
    labs_r = await db.execute(select(LabResult).where(LabResult.document_id == document_id))
    diag_r = await db.execute(select(Diagnosis).where(Diagnosis.document_id == document_id))
    algy_r = await db.execute(select(Allergy).where(Allergy.document_id == document_id))

    base.medications = [MedicationResponse.model_validate(m) for m in meds_r.scalars()]
    base.lab_results = [LabResultResponse.model_validate(l) for l in labs_r.scalars()]
    base.diagnoses = [DiagnosisResponse.model_validate(d) for d in diag_r.scalars()]
    base.allergies = [AllergyResponse.model_validate(a) for a in algy_r.scalars()]

    return base


# ---------------------------------------------------------------------------
# DELETE /documents/{document_id}
# ---------------------------------------------------------------------------


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a document from MinIO and the database (ownership verified)."""
    doc = await _load_document_or_404(db, document_id, current_user)

    storage_path = doc.storage_path

    # Delete from MinIO first; if it fails we surface the error before touching DB.
    try:
        delete_file(storage_path)
    except Exception as exc:
        logger.error(
            "MinIO delete failed during document deletion",
            extra={"document_id": str(document_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable — please retry",
        ) from exc

    await db.delete(doc)
    await db.commit()

    logger.info(
        "Document deleted",
        extra={"document_id": str(document_id), "member_id": str(doc.member_id)},
    )


# ---------------------------------------------------------------------------
# POST /documents/{document_id}/retry
# ---------------------------------------------------------------------------


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentResponse:
    """Retry extraction for a FAILED or MANUAL_REVIEW document (ownership verified).

    Returns 409 if the document is not in a retryable status.
    """
    doc = await _load_document_or_404(db, document_id, current_user)

    _retryable_statuses = {document_service.FAILED, document_service.MANUAL_REVIEW}
    if doc.processing_status not in _retryable_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Document cannot be retried from status {doc.processing_status!r}. "
                f"Allowed statuses: {sorted(_retryable_statuses)}"
            ),
        )

    await document_service.mark_queued_for_retry(db, doc.document_id)
    await db.refresh(doc)

    from app.workers.extraction_tasks import extract_document  # noqa: PLC0415

    extract_document.apply_async(args=[str(document_id)], queue="extraction")

    logger.info(
        "Document queued for retry",
        extra={"document_id": str(document_id)},
    )

    return _document_to_response(doc)


# ---------------------------------------------------------------------------
# GET /documents/{document_id}/status
# ---------------------------------------------------------------------------


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentStatusResponse:
    """Return the processing status fields for a document (ownership verified)."""
    doc = await _load_document_or_404(db, document_id, current_user)

    return DocumentStatusResponse(
        document_id=str(doc.document_id),
        processing_status=doc.processing_status,
        extraction_attempts=doc.extraction_attempts or 0,
        has_text_layer=doc.has_text_layer,
        extraction_library=doc.extraction_library,
        processed_at=doc.processed_at,
    )
