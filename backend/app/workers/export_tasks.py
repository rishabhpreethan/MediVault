"""Celery task: generate a full health-data export ZIP for a user."""
from __future__ import annotations

import asyncio
import io
import json
import logging
import uuid
import zipfile
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from celery.utils.log import get_task_logger

from app.config import settings
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# S3/MinIO helpers (mirrors extraction_tasks.py pattern)
# ---------------------------------------------------------------------------


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def _fetch_pdf_bytes_safe(s3, storage_path: str) -> Optional[bytes]:
    """Fetch PDF bytes from MinIO; return None on error (don't abort the export)."""
    try:
        response = s3.get_object(Bucket=settings.minio_bucket, Key=storage_path)
        return response["Body"].read()
    except ClientError as exc:
        logger.warning(
            "Could not fetch PDF for export",
            extra={"storage_path": storage_path, "error": str(exc)},
        )
        return None


def _upload_zip(zip_bytes: bytes, export_key: str) -> None:
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=settings.minio_bucket,
        Key=export_key,
        Body=zip_bytes,
        ContentType="application/zip",
    )


def _generate_presigned_url(export_key: str, expiry_seconds: int = 3600) -> str:
    s3 = _get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": export_key},
        ExpiresIn=expiry_seconds,
    )


# ---------------------------------------------------------------------------
# Async DB collection
# ---------------------------------------------------------------------------


def _row_to_dict(obj: Any) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model instance to a JSON-safe dict."""
    result: Dict[str, Any] = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        elif hasattr(val, "__str__") and not isinstance(val, (str, int, float, bool, type(None))):
            val = str(val)
        result[col.name] = val
    return result


async def _collect_health_data(user_id: str) -> tuple:
    """Query all health data for all family members of user_id.

    Returns (health_data_dict, list_of_storage_paths).
    No PHI is logged — only user_id, counts, and job metadata.
    """
    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.allergy import Allergy  # noqa: PLC0415
    from app.models.diagnosis import Diagnosis  # noqa: PLC0415
    from app.models.document import Document  # noqa: PLC0415
    from app.models.family_member import FamilyMember  # noqa: PLC0415
    from app.models.lab_result import LabResult  # noqa: PLC0415
    from app.models.medication import Medication  # noqa: PLC0415
    from app.models.vital import Vital  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    user_uuid = uuid.UUID(user_id)

    async with AsyncSessionLocal() as session:
        # Load all family members
        members_result = await session.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_uuid)
        )
        members: List[FamilyMember] = list(members_result.scalars().all())

        member_ids = [m.member_id for m in members]
        member_count = len(member_ids)

        if not member_ids:
            logger.info(
                "Export: no family members found",
                extra={"user_id": user_id, "member_count": 0},
            )
            return {"members": [], "export_meta": {"user_id": user_id}}, []

        health_data: Dict[str, Any] = {
            "export_meta": {"user_id": user_id},
            "members": [],
        }
        storage_paths: List[str] = []

        for member in members:
            mid = member.member_id

            meds_res = await session.execute(
                select(Medication).where(Medication.member_id == mid)
            )
            labs_res = await session.execute(
                select(LabResult).where(LabResult.member_id == mid)
            )
            diags_res = await session.execute(
                select(Diagnosis).where(Diagnosis.member_id == mid)
            )
            allergies_res = await session.execute(
                select(Allergy).where(Allergy.member_id == mid)
            )
            vitals_res = await session.execute(
                select(Vital).where(Vital.member_id == mid)
            )
            docs_res = await session.execute(
                select(Document).where(Document.member_id == mid)
            )

            docs = list(docs_res.scalars().all())
            for doc in docs:
                storage_paths.append(doc.storage_path)

            health_data["members"].append(
                {
                    "member_id": str(mid),
                    "medications": [_row_to_dict(r) for r in meds_res.scalars().all()],
                    "lab_results": [_row_to_dict(r) for r in labs_res.scalars().all()],
                    "diagnoses": [_row_to_dict(r) for r in diags_res.scalars().all()],
                    "allergies": [_row_to_dict(r) for r in allergies_res.scalars().all()],
                    "vitals": [_row_to_dict(r) for r in vitals_res.scalars().all()],
                    "documents": [_row_to_dict(d) for d in docs],
                }
            )

        logger.info(
            "Export: health data collected",
            extra={"user_id": user_id, "member_count": member_count},
        )
        return health_data, storage_paths


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="export.generate_user_export",
    queue="default",
    max_retries=2,
    default_retry_delay=15,
)
def generate_user_export(self, user_id: str, job_id: str) -> Dict[str, Any]:
    """Build a ZIP export of all health data + PDFs for a user.

    Steps:
    1. Collect all health entity rows for every family member → health_data.json
    2. Download each PDF from MinIO
    3. Build an in-memory ZIP (health_data.json + PDFs)
    4. Upload ZIP to MinIO under exports/{user_id}/{job_id}.zip
    5. Generate a 1-hour pre-signed download URL
    6. Return {"status": "COMPLETE", "download_url": "..."}

    Email is OUT OF SCOPE — logs a placeholder instead.
    """
    logger.info(
        "generate_user_export started",
        extra={"user_id": user_id, "job_id": job_id},
    )

    try:
        # -- 1. Collect health data ------------------------------------------
        health_data, storage_paths = asyncio.run(
            _collect_health_data(user_id)
        )

        # -- 2. Build in-memory ZIP ------------------------------------------
        zip_buffer = io.BytesIO()
        s3 = _get_s3_client()

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # health_data.json
            zf.writestr(
                "health_data.json",
                json.dumps(health_data, indent=2, default=str),
            )

            # PDFs from MinIO
            for storage_path in storage_paths:
                pdf_bytes = _fetch_pdf_bytes_safe(s3, storage_path)
                if pdf_bytes is not None:
                    # Use original storage_path as the filename inside ZIP
                    arcname = f"pdfs/{storage_path.replace('/', '_')}.pdf"
                    zf.writestr(arcname, pdf_bytes)

        zip_bytes = zip_buffer.getvalue()

        # -- 3. Upload ZIP to MinIO ------------------------------------------
        export_key = f"exports/{user_id}/{job_id}.zip"
        _upload_zip(zip_bytes, export_key)

        logger.info(
            "generate_user_export: ZIP uploaded",
            extra={"user_id": user_id, "job_id": job_id},
        )

        # -- 4. Generate pre-signed URL (1 hour) ----------------------------
        download_url = _generate_presigned_url(export_key, expiry_seconds=3600)

        # -- 5. Email placeholder (SendGrid not yet configured) -------------
        logger.info(
            "generate_user_export: would send email — SendGrid not yet configured",
            extra={"user_id": user_id, "job_id": job_id},
        )

        return {"status": "COMPLETE", "download_url": download_url}

    except Exception as exc:
        logger.error(
            "generate_user_export failed",
            extra={"user_id": user_id, "job_id": job_id, "error": str(exc)},
        )
        raise
