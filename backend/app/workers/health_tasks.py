"""Worker health-check task and account-purge task (MV-110).

Used by the /api/v1/health endpoint and the docker-compose healthcheck
to verify the Celery worker is alive and connected to the broker.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import List

import boto3
from botocore.exceptions import ClientError
from celery.utils.log import get_task_logger

from app.config import settings
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="worker.ping", queue="default")
def ping() -> str:
    """Lightweight liveness check. Returns 'pong'."""
    return "pong"


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def _delete_minio_object(s3_client, storage_path: str) -> None:
    """Delete a single object from MinIO, ignoring NoSuchKey errors."""
    try:
        s3_client.delete_object(Bucket=settings.minio_bucket, Key=storage_path)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code != "NoSuchKey":
            logger.warning(
                "MinIO delete failed",
                extra={"storage_path_hash": hash(storage_path), "error_code": error_code},
            )


async def _run_purge(user_id_str: str) -> dict:
    """Core async logic for purging all user data."""
    from sqlalchemy import select  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.document import Document  # noqa: PLC0415
    from app.models.family_member import FamilyMember  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415

    user_uuid = uuid.UUID(user_id_str)

    # Collect all storage_paths before deletion
    storage_paths: List[str] = []
    async with AsyncSessionLocal() as session:
        members_result = await session.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_uuid)
        )
        members = members_result.scalars().all()

        member_ids = [m.member_id for m in members]
        doc_count = 0

        for member_id in member_ids:
            docs_result = await session.execute(
                select(Document).where(Document.member_id == member_id)
            )
            docs = docs_result.scalars().all()
            for doc in docs:
                storage_paths.append(doc.storage_path)
                doc_count += 1

    # Delete MinIO objects (sync boto3 outside session)
    if storage_paths:
        s3 = _get_s3_client()
        for path in storage_paths:
            _delete_minio_object(s3, path)

    logger.info(
        "purge_user_data: MinIO objects deleted",
        extra={"user_id": user_id_str, "object_count": len(storage_paths)},
    )

    # Hard-delete FamilyMember rows (cascade handles child records)
    deleted_member_count = 0
    async with AsyncSessionLocal() as session:
        members_result = await session.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_uuid)
        )
        members = members_result.scalars().all()
        deleted_member_count = len(members)
        for member in members:
            await session.delete(member)
        await session.commit()

    logger.info(
        "purge_user_data: FamilyMember rows deleted",
        extra={"user_id": user_id_str, "member_count": deleted_member_count},
    )

    # Ensure user remains inactive (idempotent)
    async with AsyncSessionLocal() as session:
        user_result = await session.execute(
            select(User).where(User.user_id == user_uuid)
        )
        user = user_result.scalar_one_or_none()
        if user is not None:
            user.is_active = False
            await session.commit()

    logger.info(
        "purge_user_data: complete",
        extra={
            "user_id": user_id_str,
            "member_count": deleted_member_count,
            "document_count": doc_count,
        },
    )

    return {
        "user_id": user_id_str,
        "status": "PURGED",
        "member_count": deleted_member_count,
        "document_count": doc_count,
    }


@celery_app.task(
    bind=True,
    name="worker.purge_user_data",
    queue="default",
    max_retries=3,
    default_retry_delay=60,
)
def purge_user_data(self, user_id: str) -> dict:
    """Asynchronously purge all data for a deleted user account.

    - Deletes all documents from MinIO (iterates family members → documents → storage_path)
    - Hard-deletes all FamilyMember rows (cascade handles child records)
    - Ensures user.is_active = False (idempotent)

    Args:
        user_id: UUID string of the User record.

    Returns:
        dict with keys: user_id, status, member_count, document_count
    """
    logger.info("purge_user_data started", extra={"user_id": user_id})
    try:
        return asyncio.run(_run_purge(user_id))
    except Exception as exc:
        logger.error(
            "purge_user_data failed",
            extra={"user_id": user_id, "attempt": self.request.retries + 1},
        )
        raise self.retry(exc=exc)
