"""Unit tests for export_tasks helpers (MV-111)."""
from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub boto3 / botocore before any app imports
for _mod in ("boto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        _fake = ModuleType(_mod)
        if _mod == "botocore.exceptions":
            _fake.ClientError = Exception  # type: ignore[attr-defined]
        sys.modules[_mod] = _fake

from app.workers.export_tasks import (  # noqa: E402
    _collect_health_data,
    _fetch_pdf_bytes_safe,
    _row_to_dict,
)


# ---------------------------------------------------------------------------
# _row_to_dict
# ---------------------------------------------------------------------------


class TestRowToDict:
    def _make_col(self, name: str):
        col = MagicMock()
        col.name = name
        return col

    def _make_obj(self, **fields):
        """Create a mock ORM row with __table__.columns and field attributes."""
        obj = MagicMock()
        obj.__table__ = MagicMock()
        obj.__table__.columns = [self._make_col(k) for k in fields]
        for k, v in fields.items():
            setattr(obj, k, v)
        return obj

    def test_string_field_is_preserved(self):
        obj = self._make_obj(name="Ibuprofen")
        result = _row_to_dict(obj)
        assert result["name"] == "Ibuprofen"

    def test_int_field_is_preserved(self):
        obj = self._make_obj(count=42)
        result = _row_to_dict(obj)
        assert result["count"] == 42

    def test_none_field_is_preserved(self):
        obj = self._make_obj(optional=None)
        result = _row_to_dict(obj)
        assert result["optional"] is None

    def test_datetime_is_iso_formatted(self):
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        obj = self._make_obj(created_at=dt)
        result = _row_to_dict(obj)
        assert result["created_at"] == dt.isoformat()

    def test_date_is_iso_formatted(self):
        d = date(2024, 3, 15)
        obj = self._make_obj(test_date=d)
        result = _row_to_dict(obj)
        assert result["test_date"] == d.isoformat()

    def test_uuid_is_string(self):
        uid = uuid.uuid4()
        obj = self._make_obj(doc_id=uid)
        result = _row_to_dict(obj)
        assert result["doc_id"] == str(uid)

    def test_multiple_fields(self):
        obj = self._make_obj(name="test", value=1.5, active=True)
        result = _row_to_dict(obj)
        assert result == {"name": "test", "value": 1.5, "active": True}


# ---------------------------------------------------------------------------
# _fetch_pdf_bytes_safe
# ---------------------------------------------------------------------------


class TestFetchPdfBytesSafe:
    def test_returns_bytes_on_success(self):
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=b"%PDF-1.4"))}
        result = _fetch_pdf_bytes_safe(s3, "members/abc/doc.pdf")
        assert result == b"%PDF-1.4"

    def test_returns_none_on_client_error(self):
        from botocore.exceptions import ClientError

        s3 = MagicMock()
        s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )
        result = _fetch_pdf_bytes_safe(s3, "missing/path.pdf")
        assert result is None


# ---------------------------------------------------------------------------
# _collect_health_data
# ---------------------------------------------------------------------------


class TestCollectHealthData:
    @pytest.mark.asyncio
    async def test_returns_empty_members_when_none_found(self):
        """When user has no family members, returns empty members list."""
        user_id = str(uuid.uuid4())

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        empty_result = MagicMock()
        empty_scalars = MagicMock()
        empty_scalars.all.return_value = []
        empty_result.scalars.return_value = empty_scalars
        mock_session.execute = AsyncMock(return_value=empty_result)

        with patch("app.database.AsyncSessionLocal", return_value=mock_session):
            health_data, storage_paths = await _collect_health_data(user_id)

        assert health_data["members"] == []
        assert storage_paths == []
        assert health_data["export_meta"]["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_collects_data_for_one_member(self):
        """With one member and one document, returns member dict and storage path."""
        user_id = str(uuid.uuid4())
        member_id = uuid.uuid4()

        mock_member = MagicMock()
        mock_member.member_id = member_id

        mock_doc = MagicMock()
        mock_doc.storage_path = "members/abc/report.pdf"
        mock_doc.__table__ = MagicMock()
        mock_doc.__table__.columns = []

        call_n = {"n": 0}

        async def _fake_execute(stmt):
            result = MagicMock()
            scalars = MagicMock()
            call_n["n"] += 1
            if call_n["n"] == 1:
                # FamilyMember query
                scalars.all.return_value = [mock_member]
            elif call_n["n"] == 7:
                # Document query (6th per-member query)
                scalars.all.return_value = [mock_doc]
            else:
                scalars.all.return_value = []
            result.scalars.return_value = scalars
            return result

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = _fake_execute

        with patch("app.database.AsyncSessionLocal", return_value=mock_session):
            health_data, storage_paths = await _collect_health_data(user_id)

        assert len(health_data["members"]) == 1
        assert health_data["members"][0]["member_id"] == str(member_id)
        assert "members/abc/report.pdf" in storage_paths
