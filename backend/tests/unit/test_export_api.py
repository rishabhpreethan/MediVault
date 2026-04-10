"""Unit tests for the export API (MV-111).

Tests exercise endpoint logic directly without TestClient; Celery and DB are
fully mocked so no real infrastructure is required.
"""
from __future__ import annotations

import sys
import uuid
from types import ModuleType
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Stub out boto3 / botocore before any app imports so storage modules load fine
# ---------------------------------------------------------------------------
if "boto3" not in sys.modules:
    _fake_boto3 = ModuleType("boto3")
    _fake_boto3.client = MagicMock()  # type: ignore[attr-defined]
    sys.modules["boto3"] = _fake_boto3
if "botocore" not in sys.modules:
    _fake_botocore = ModuleType("botocore")
    _botocore_exc = ModuleType("botocore.exceptions")
    _botocore_exc.ClientError = Exception  # type: ignore[attr-defined]
    sys.modules["botocore"] = _fake_botocore
    sys.modules["botocore.exceptions"] = _botocore_exc


# ---------------------------------------------------------------------------
# Import the module under test AFTER stubs are in place
# ---------------------------------------------------------------------------
from app.api.export import (  # noqa: E402
    _EXPORT_JOBS,
    _sync_celery_result,
    get_export_status,
    request_all_export,
    request_member_export,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: Optional[uuid.UUID] = None):
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    return user


def _make_member(user_id: Optional[uuid.UUID] = None, member_id: Optional[uuid.UUID] = None):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    return member


def _make_db_returning(value):
    """Return a mock AsyncSession whose execute() gives back `value`."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = value
    db.execute = AsyncMock(return_value=scalar_result)
    return db


# ---------------------------------------------------------------------------
# Test 1: request_all_export queues a job and returns 202 payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_all_export_queues_job():
    """POST /export/request-all should register a PENDING job and return job_id."""
    user = _make_user()
    db = _make_db_returning(None)  # not used by request_all_export

    mock_task = MagicMock()
    mock_task.id = str(uuid.uuid4())

    mock_gen = MagicMock()
    mock_gen.apply_async.return_value = mock_task

    # The function does a local import: from app.workers.export_tasks import generate_user_export
    # Patch the source so the local import gets the mock.
    with patch("app.workers.export_tasks.generate_user_export", mock_gen):
        result = await request_all_export(current_user=user, db=db)

    assert "job_id" in result
    assert result["message"] == "Export queued"
    job_id = result["job_id"]
    assert job_id in _EXPORT_JOBS
    assert _EXPORT_JOBS[job_id]["status"] == "PENDING"

    # Cleanup
    del _EXPORT_JOBS[job_id]


# ---------------------------------------------------------------------------
# Test 2: request_member_export with valid member queues a job
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_member_export_valid_member():
    """POST /export/request?member_id=... with owned member should queue job."""
    user = _make_user()
    member = _make_member(user_id=user.user_id)
    db = _make_db_returning(member)

    mock_task = MagicMock()
    mock_task.id = str(uuid.uuid4())

    mock_gen = MagicMock()
    mock_gen.apply_async.return_value = mock_task

    with patch("app.workers.export_tasks.generate_user_export", mock_gen):
        result = await request_member_export(
            current_user=user, db=db, member_id=member.member_id
        )

    assert "job_id" in result
    assert result["message"] == "Export queued"
    job_id = result["job_id"]
    assert _EXPORT_JOBS[job_id]["status"] == "PENDING"

    # Cleanup
    del _EXPORT_JOBS[job_id]


# ---------------------------------------------------------------------------
# Test 3: request_member_export returns 403 for unowned member
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_member_export_forbidden():
    """POST /export/request?member_id=... with someone else's member → 403."""
    user = _make_user()
    other_user_id = uuid.uuid4()
    member = _make_member(user_id=other_user_id)  # different owner
    db = _make_db_returning(member)

    with pytest.raises(HTTPException) as exc_info:
        await request_member_export(
            current_user=user, db=db, member_id=member.member_id
        )

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 4: get_export_status returns PENDING while job is in-flight
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_pending():
    """GET /export/status/{job_id} returns PENDING when job not finished."""
    user = _make_user()
    db = _make_db_returning(None)
    job_id = str(uuid.uuid4())
    _EXPORT_JOBS[job_id] = {"status": "PENDING", "download_url": None}

    # No celery_task_id → _sync_celery_result is skipped
    result = await get_export_status(job_id=job_id, current_user=user, db=db)

    assert result["status"] == "PENDING"
    assert result["download_url"] is None

    # Cleanup
    del _EXPORT_JOBS[job_id]


# ---------------------------------------------------------------------------
# Test 5: get_export_status updates to COMPLETE via Celery result sync
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_complete_after_sync():
    """GET /export/status/{job_id} syncs Celery result and returns COMPLETE."""
    user = _make_user()
    db = _make_db_returning(None)
    job_id = str(uuid.uuid4())
    celery_task_id = str(uuid.uuid4())
    expected_url = "https://minio.example.com/exports/test.zip?X-Amz-Signature=abc"

    _EXPORT_JOBS[job_id] = {
        "status": "PENDING",
        "download_url": None,
        "celery_task_id": celery_task_id,
    }

    mock_async_result = MagicMock()
    mock_async_result.successful.return_value = True
    mock_async_result.failed.return_value = False
    mock_async_result.result = {"status": "COMPLETE", "download_url": expected_url}

    with patch("app.api.export.AsyncResult", return_value=mock_async_result):
        result = await get_export_status(job_id=job_id, current_user=user, db=db)

    assert result["status"] == "COMPLETE"
    assert result["download_url"] == expected_url
    assert _EXPORT_JOBS[job_id]["status"] == "COMPLETE"

    # Cleanup
    del _EXPORT_JOBS[job_id]


# ---------------------------------------------------------------------------
# Test 6: get_export_status returns 404 for unknown job_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_not_found():
    """GET /export/status/<unknown> → 404."""
    user = _make_user()
    db = _make_db_returning(None)
    unknown_id = str(uuid.uuid4())

    # Ensure key does not exist
    _EXPORT_JOBS.pop(unknown_id, None)

    with pytest.raises(HTTPException) as exc_info:
        await get_export_status(job_id=unknown_id, current_user=user, db=db)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 7: get_export_status marks FAILED when Celery task failed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_failed():
    """GET /export/status/{job_id} syncs Celery result and returns FAILED."""
    user = _make_user()
    db = _make_db_returning(None)
    job_id = str(uuid.uuid4())
    celery_task_id = str(uuid.uuid4())

    _EXPORT_JOBS[job_id] = {
        "status": "PENDING",
        "download_url": None,
        "celery_task_id": celery_task_id,
    }

    mock_async_result = MagicMock()
    mock_async_result.successful.return_value = False
    mock_async_result.failed.return_value = True

    with patch("app.api.export.AsyncResult", return_value=mock_async_result):
        result = await get_export_status(job_id=job_id, current_user=user, db=db)

    assert result["status"] == "FAILED"
    assert result["download_url"] is None

    # Cleanup
    del _EXPORT_JOBS[job_id]
