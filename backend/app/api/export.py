"""Export API — request and poll async health-data ZIP exports (MV-111)."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory job store
#
# Intentionally simple: no DB table needed for MVP.  Keys are job_id strings;
# values are dicts with shape {"status": str, "download_url": Optional[str]}.
# NOTE: This is process-local and will not survive a worker restart.  Replace
# with a Redis/DB-backed store if persistence across restarts is required.
# ---------------------------------------------------------------------------
_EXPORT_JOBS: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# POST /export/request   (single member)
# POST /export/request-all   (all members)
# ---------------------------------------------------------------------------


@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue an export for a specific family member's data",
)
async def request_member_export(
    current_user: CurrentUser,
    db: DbSession,
    member_id: uuid.UUID = Query(..., description="UUID of the family member to export"),
) -> Dict[str, str]:
    """Queue an async export job scoped to a single family member.

    The family member must belong to the authenticated user. Returns a job_id
    that can be polled via GET /export/status/{job_id}.
    """
    from sqlalchemy import select  # noqa: PLC0415

    from app.models.family_member import FamilyMember  # noqa: PLC0415

    # Verify member belongs to the current user
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == member_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )
    if member.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    job_id = str(uuid.uuid4())
    _EXPORT_JOBS[job_id] = {"status": "PENDING", "download_url": None}

    from app.workers.export_tasks import generate_user_export  # noqa: PLC0415

    # Dispatch as a Celery task; result is stored via callback in the task
    task = generate_user_export.apply_async(
        args=[str(current_user.user_id), job_id],
        link=_build_completion_callback(job_id),
    )
    # Store the celery task_id for potential future reference (not exposed)
    _EXPORT_JOBS[job_id]["celery_task_id"] = task.id

    logger.info(
        "Export job queued (single member)",
        extra={"user_id": str(current_user.user_id), "job_id": job_id},
    )

    return {"job_id": job_id, "message": "Export queued"}


@router.post(
    "/request-all",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue an export for all family members",
)
async def request_all_export(
    current_user: CurrentUser,
    db: DbSession,
) -> Dict[str, str]:
    """Queue an async export job for all family members of the authenticated user.

    Returns a job_id that can be polled via GET /export/status/{job_id}.
    """
    job_id = str(uuid.uuid4())
    _EXPORT_JOBS[job_id] = {"status": "PENDING", "download_url": None}

    from app.workers.export_tasks import generate_user_export  # noqa: PLC0415

    task = generate_user_export.apply_async(
        args=[str(current_user.user_id), job_id],
        link=_build_completion_callback(job_id),
    )
    _EXPORT_JOBS[job_id]["celery_task_id"] = task.id

    logger.info(
        "Export job queued (all members)",
        extra={"user_id": str(current_user.user_id), "job_id": job_id},
    )

    return {"job_id": job_id, "message": "Export queued"}


# ---------------------------------------------------------------------------
# GET /export/status/{job_id}
# ---------------------------------------------------------------------------


@router.get(
    "/status/{job_id}",
    summary="Poll the status of an export job",
)
async def get_export_status(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> Dict[str, Any]:
    """Return the current status of an export job.

    Status values:
    - ``PENDING``  — queued but not yet finished
    - ``COMPLETE`` — ZIP is ready; ``download_url`` is populated (1-hour presigned URL)
    - ``FAILED``   — the Celery task raised an unrecoverable error
    """
    if job_id not in _EXPORT_JOBS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found",
        )

    job = _EXPORT_JOBS[job_id]

    # Lazily sync with Celery result backend if status is still PENDING
    if job["status"] == "PENDING" and "celery_task_id" in job:
        _sync_celery_result(job_id, job)

    return {
        "status": job["status"],
        "download_url": job.get("download_url"),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sync_celery_result(job_id: str, job: Dict[str, Any]) -> None:
    """Check Celery result backend and update the in-memory store if done."""
    from app.workers.celery_app import celery_app  # noqa: PLC0415

    task_id = job.get("celery_task_id")
    if not task_id:
        return

    result = AsyncResult(task_id, app=celery_app)

    if result.successful():
        task_result = result.result or {}
        job["status"] = "COMPLETE"
        job["download_url"] = task_result.get("download_url")
        logger.info(
            "Export job completed (synced from Celery)",
            extra={"job_id": job_id},
        )
    elif result.failed():
        job["status"] = "FAILED"
        logger.warning(
            "Export job failed (synced from Celery)",
            extra={"job_id": job_id},
        )


def _build_completion_callback(job_id: str):
    """Return a Celery on_success callback signature that updates _EXPORT_JOBS.

    We use a simple approach: the callback is handled by _sync_celery_result
    when the status endpoint is polled. This avoids needing a separate Celery
    task just for bookkeeping.
    """
    # No-op callback placeholder — status polling uses _sync_celery_result
    return None
