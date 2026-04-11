"""Unit tests for the documents API business logic (MV-021).

Tests exercise the helper functions and validation paths directly without
using TestClient (which has a greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import io
import sys
import uuid
from types import ModuleType
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# Inject fake boto3 / botocore so storage_service can be imported without the
# real packages installed locally (they're available inside Docker).
if "boto3" not in sys.modules:
    _fake_boto3 = ModuleType("boto3")
    _fake_boto3.client = MagicMock()  # type: ignore[attr-defined]
    sys.modules["boto3"] = _fake_boto3
if "botocore" not in sys.modules:
    _fake_botocore = ModuleType("botocore")
    _fake_botocore_exc = ModuleType("botocore.exceptions")
    _fake_botocore_exc.ClientError = Exception  # type: ignore[attr-defined]
    sys.modules["botocore"] = _fake_botocore
    sys.modules["botocore.exceptions"] = _fake_botocore_exc

from fastapi import Request

from app.api.documents import (
    _MAX_FILE_SIZE,
    _document_to_response,
    _load_document_or_404,
    _load_member_or_404,
    retry_document,
    upload_document,
)

_MOCK_REQUEST = MagicMock(spec=Request)
_MOCK_REQUEST.client = MagicMock()
_MOCK_REQUEST.client.host = "127.0.0.1"
_MOCK_REQUEST.headers = {}


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: uuid.UUID | None = None):
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    return user


def _make_member(user_id: uuid.UUID | None = None, member_id: uuid.UUID | None = None):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    return member


def _make_document(
    user_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
):
    from app.models.document import Document

    doc = MagicMock(spec=Document)
    doc.document_id = document_id or uuid.uuid4()
    doc.member_id = member_id or uuid.uuid4()
    doc.user_id = user_id or uuid.uuid4()
    doc.document_type = "LAB_REPORT"
    doc.document_date = date(2025, 1, 1)
    doc.original_filename = "report.pdf"
    doc.file_size_bytes = 1024
    doc.processing_status = "QUEUED"
    doc.has_text_layer = None
    doc.extraction_library = None
    doc.uploaded_at = datetime.now(tz=timezone.utc)
    doc.processed_at = None
    doc.storage_path = "user/member/doc.pdf"
    return doc


def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


# ---------------------------------------------------------------------------
# Tests: _load_member_or_404
# ---------------------------------------------------------------------------


class TestLoadMemberOr404:
    @pytest.mark.asyncio
    async def test_returns_member_when_owner(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        result = await _load_member_or_404(db, member.member_id, user)

        assert result is member

    @pytest.mark.asyncio
    async def test_raises_404_when_member_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await _load_member_or_404(db, uuid.uuid4(), user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403_when_member_belongs_to_other_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        with pytest.raises(HTTPException) as exc_info:
            await _load_member_or_404(db, member.member_id, user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: _load_document_or_404
# ---------------------------------------------------------------------------


class TestLoadDocumentOr404:
    @pytest.mark.asyncio
    async def test_returns_document_when_owner(self):
        user = _make_user()
        doc = _make_document(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(doc))

        result = await _load_document_or_404(db, doc.document_id, user)

        assert result is doc

    @pytest.mark.asyncio
    async def test_raises_404_when_document_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(None))

        with pytest.raises(HTTPException) as exc_info:
            await _load_document_or_404(db, uuid.uuid4(), user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403_when_document_belongs_to_other_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        doc = _make_document(user_id=other_user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(doc))

        with pytest.raises(HTTPException) as exc_info:
            await _load_document_or_404(db, doc.document_id, user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: upload_document — validation paths
# ---------------------------------------------------------------------------


def _make_upload_file(
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
    content: bytes = b"%PDF-1.4 test",
) -> MagicMock:
    upload_file = MagicMock()
    upload_file.filename = filename
    upload_file.content_type = content_type
    upload_file.read = AsyncMock(return_value=content)
    return upload_file


class TestUploadDocumentValidation:
    @pytest.mark.asyncio
    async def test_raises_400_for_non_pdf_content_type(self):
        user = _make_user()
        db = _mock_db()
        upload_file = _make_upload_file(
            filename="report.pdf",
            content_type="application/octet-stream",
        )

        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=uuid.uuid4(),
                document_type="LAB_REPORT",
                document_date=None,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_for_non_pdf_extension(self):
        user = _make_user()
        db = _mock_db()
        upload_file = _make_upload_file(
            filename="report.docx",
            content_type="application/pdf",
        )

        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=uuid.uuid4(),
                document_type="LAB_REPORT",
                document_date=None,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_for_file_exceeding_size_limit(self):
        user = _make_user()
        db = _mock_db()
        oversized_bytes = b"x" * (_MAX_FILE_SIZE + 1)
        upload_file = _make_upload_file(content=oversized_bytes)

        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=uuid.uuid4(),
                document_type="LAB_REPORT",
                document_date=None,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_422_for_invalid_document_type(self):
        user = _make_user()
        db = _mock_db()
        upload_file = _make_upload_file()

        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=uuid.uuid4(),
                document_type="INVALID_TYPE",
                document_date=None,
            )

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_raises_403_when_member_not_owned_by_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))
        upload_file = _make_upload_file()

        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=member.member_id,
                document_type="LAB_REPORT",
                document_date=None,
            )

        assert exc_info.value.status_code == 403


class TestUploadDocumentSuccess:
    @pytest.mark.asyncio
    async def test_valid_upload_creates_document_and_queues_task(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        # After db.refresh, simulate the document having its data set.
        captured_doc: list = []

        def capture_add(obj):
            captured_doc.append(obj)

        db.add = MagicMock(side_effect=capture_add)

        upload_file = _make_upload_file()

        with (
            patch("app.api.documents.upload_pdf") as mock_upload,
            patch("app.workers.extraction_tasks.extract_document") as mock_task,
        ):
            mock_task.apply_async = MagicMock()

            # db.refresh does nothing, but we need the doc to have the right fields.
            # Since Document() is constructed inside the handler we patch db.refresh
            # to add the fields we need for _document_to_response.
            async def mock_refresh(obj):
                # Simulate what the DB sets on INSERT (server_default fields)
                from datetime import datetime, timezone  # noqa: PLC0415
                if not getattr(obj, "uploaded_at", None):
                    obj.uploaded_at = datetime.now(tz=timezone.utc)

            db.refresh = AsyncMock(side_effect=mock_refresh)

            response = await upload_document(
                request=_MOCK_REQUEST,
                current_user=user,
                db=db,
                file=upload_file,
                member_id=member.member_id,
                document_type="LAB_REPORT",
                document_date="2025-06-01",
            )

        # DB add and commit must be called.
        db.add.assert_called_once()
        db.commit.assert_called()

        # MinIO upload must be called.
        mock_upload.assert_called_once()

        # Celery task must be dispatched.
        mock_task.apply_async.assert_called_once()
        task_args = mock_task.apply_async.call_args
        assert task_args.kwargs.get("queue") == "extraction" or (
            task_args[1].get("queue") == "extraction"
            if task_args[1]
            else task_args.kwargs.get("queue") == "extraction"
        )

        # Response should reflect QUEUED status.
        assert response.processing_status == "QUEUED"
        assert response.document_type == "LAB_REPORT"
        assert response.document_date == date(2025, 6, 1)

    @pytest.mark.asyncio
    async def test_storage_failure_rolls_back_db_record(self):
        from botocore.exceptions import ClientError

        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(member))

        upload_file = _make_upload_file()

        with patch(
            "app.api.documents.upload_pdf",
            side_effect=ClientError({"Error": {"Code": "500", "Message": "err"}}, "put_object"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    request=_MOCK_REQUEST,
                    current_user=user,
                    db=db,
                    file=upload_file,
                    member_id=member.member_id,
                    document_type="LAB_REPORT",
                    document_date=None,
                )

        assert exc_info.value.status_code == 503
        # db.delete must be called to roll back the orphaned record.
        db.delete.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: _document_to_response
# ---------------------------------------------------------------------------


class TestDocumentToResponse:
    def test_converts_uuids_to_strings(self):
        doc = _make_document()
        response = _document_to_response(doc)

        assert isinstance(response.document_id, str)
        assert isinstance(response.member_id, str)
        assert str(doc.document_id) == response.document_id
        assert str(doc.member_id) == response.member_id

    def test_processing_status_preserved(self):
        doc = _make_document()
        doc.processing_status = "COMPLETE"
        response = _document_to_response(doc)

        assert response.processing_status == "COMPLETE"

    def test_optional_fields_default_when_none(self):
        doc = _make_document()
        doc.has_text_layer = None
        doc.extraction_library = None
        doc.processed_at = None
        doc.document_date = None
        response = _document_to_response(doc)

        assert response.has_text_layer is None
        assert response.extraction_library is None
        assert response.processed_at is None
        assert response.document_date is None


# ---------------------------------------------------------------------------
# Tests: retry_document endpoint
# ---------------------------------------------------------------------------


class TestRetryEndpoint:
    @pytest.mark.asyncio
    async def test_retry_raises_409_when_not_failed(self):
        """A document with status COMPLETE must yield 409 on retry."""
        user = _make_user()
        doc = _make_document(user_id=user.user_id)
        doc.processing_status = "COMPLETE"
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(doc))

        with pytest.raises(HTTPException) as exc_info:
            await retry_document(
                document_id=doc.document_id,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_retry_succeeds_when_failed(self):
        """A FAILED document can be retried — mark_queued_for_retry and task dispatch called."""
        user = _make_user()
        doc = _make_document(user_id=user.user_id)
        doc.processing_status = "FAILED"
        doc.extraction_attempts = 1
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(doc))

        with (
            patch(
                "app.services.document_service.mark_queued_for_retry",
                new_callable=AsyncMock,
            ) as mock_retry,
            patch("app.workers.extraction_tasks.extract_document") as mock_task,
        ):
            mock_task.apply_async = MagicMock()

            response = await retry_document(
                document_id=doc.document_id,
                current_user=user,
                db=db,
            )

        mock_retry.assert_awaited_once()
        mock_task.apply_async.assert_called_once()
        task_call_kwargs = mock_task.apply_async.call_args
        assert task_call_kwargs.kwargs.get("queue") == "extraction" or (
            task_call_kwargs[1].get("queue") == "extraction"
            if task_call_kwargs[1]
            else task_call_kwargs.kwargs.get("queue") == "extraction"
        )
        assert response.processing_status == "FAILED"  # mock doc status unchanged in test

    @pytest.mark.asyncio
    async def test_retry_succeeds_when_manual_review(self):
        """A MANUAL_REVIEW document can also be retried."""
        user = _make_user()
        doc = _make_document(user_id=user.user_id)
        doc.processing_status = "MANUAL_REVIEW"
        doc.extraction_attempts = 3
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result(doc))

        with (
            patch(
                "app.services.document_service.mark_queued_for_retry",
                new_callable=AsyncMock,
            ) as mock_retry,
            patch("app.workers.extraction_tasks.extract_document") as mock_task,
        ):
            mock_task.apply_async = MagicMock()

            response = await retry_document(
                document_id=doc.document_id,
                current_user=user,
                db=db,
            )

        mock_retry.assert_awaited_once()
        mock_task.apply_async.assert_called_once()
        assert response.processing_status == "MANUAL_REVIEW"  # mock doc status unchanged in test
