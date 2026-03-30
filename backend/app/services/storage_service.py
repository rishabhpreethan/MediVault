"""MinIO / S3-compatible storage helpers for MediVault documents."""
from __future__ import annotations

import io
import logging

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_s3_client():
    """Return a boto3 S3 client pointed at the configured MinIO endpoint."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def upload_pdf(pdf_bytes: bytes, storage_path: str) -> None:
    """Upload raw PDF bytes to MinIO at the given storage path.

    Args:
        pdf_bytes:    Raw bytes of the PDF document.
        storage_path: Key within the configured bucket, e.g.
                      ``{user_id}/{member_id}/{document_id}.pdf``.

    Raises:
        ClientError: If the upload to MinIO fails.
    """
    s3 = _get_s3_client()
    try:
        s3.put_object(
            Bucket=settings.minio_bucket,
            Key=storage_path,
            Body=io.BytesIO(pdf_bytes),
            ContentType="application/pdf",
        )
    except ClientError as exc:
        logger.error(
            "MinIO upload failed",
            extra={"storage_path": storage_path, "error": str(exc)},
        )
        raise


def delete_file(storage_path: str) -> None:
    """Delete an object from MinIO.

    Args:
        storage_path: Key of the object to delete within the configured bucket.

    Raises:
        ClientError: If the deletion request fails for a reason other than the
                     object being absent (a missing object is treated as a
                     no-op).
    """
    s3 = _get_s3_client()
    try:
        s3.delete_object(Bucket=settings.minio_bucket, Key=storage_path)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in ("NoSuchKey", "404"):
            # Already gone — treat as success.
            logger.warning(
                "MinIO delete: object not found (already deleted)",
                extra={"storage_path": storage_path},
            )
            return
        logger.error(
            "MinIO delete failed",
            extra={"storage_path": storage_path, "error": str(exc)},
        )
        raise
