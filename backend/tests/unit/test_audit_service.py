"""Unit tests for audit_service (FR-AUTH-009)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.audit_service import (
    EVENT_ACCOUNT_DELETION_REQUESTED,
    EVENT_LOGIN,
    EVENT_PROVISION,
    log_auth_event,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_db() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# audit_service.log_auth_event tests
# ---------------------------------------------------------------------------

class TestLogAuthEvent:
    @pytest.mark.asyncio
    async def test_log_auth_event_writes_to_db(self):
        """db.add must be called with an AuthAuditLog instance."""
        from app.models.auth_audit import AuthAuditLog

        db = _mock_db()
        await log_auth_event(db, event_type=EVENT_LOGIN, user_id=uuid.uuid4())

        db.add.assert_called_once()
        call_arg = db.add.call_args[0][0]
        assert isinstance(call_arg, AuthAuditLog)

    @pytest.mark.asyncio
    async def test_log_auth_event_swallows_exceptions(self):
        """If db.add raises, no exception should propagate to the caller."""
        db = _mock_db()
        db.add.side_effect = Exception("DB exploded")

        # Must not raise
        await log_auth_event(db, event_type=EVENT_LOGIN, user_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_log_auth_event_with_all_fields(self):
        """All supplied fields must be persisted on the AuthAuditLog instance."""
        from app.models.auth_audit import AuthAuditLog

        db = _mock_db()
        uid = uuid.uuid4()
        ip = "192.168.1.1"
        ua = "Mozilla/5.0"

        await log_auth_event(
            db,
            event_type=EVENT_PROVISION,
            user_id=uid,
            ip_address=ip,
            user_agent=ua,
        )

        db.add.assert_called_once()
        entry: AuthAuditLog = db.add.call_args[0][0]
        assert entry.user_id == uid
        assert entry.event_type == EVENT_PROVISION
        assert entry.ip_address == ip
        assert entry.user_agent == ua

    @pytest.mark.asyncio
    async def test_log_auth_event_user_id_optional(self):
        """user_id=None must be accepted without error."""
        from app.models.auth_audit import AuthAuditLog

        db = _mock_db()
        await log_auth_event(db, event_type=EVENT_PROVISION, user_id=None)

        db.add.assert_called_once()
        entry: AuthAuditLog = db.add.call_args[0][0]
        assert entry.user_id is None


# ---------------------------------------------------------------------------
# Endpoint integration tests (mock audit_service)
# ---------------------------------------------------------------------------

class TestProvisionEndpointLogsAudit:
    @pytest.mark.asyncio
    async def test_provision_endpoint_logs_provision_event(self):
        """provision_user must log PROVISION for a new user."""
        import sys
        from types import ModuleType

        # Stub boto3/botocore if not already present
        for _mod in ("boto3", "botocore", "botocore.exceptions"):
            if _mod not in sys.modules:
                fake = ModuleType(_mod)
                if _mod == "botocore.exceptions":
                    fake.ClientError = Exception  # type: ignore[attr-defined]
                sys.modules[_mod] = fake

        from fastapi import Request
        from fastapi.security import HTTPAuthorizationCredentials
        from app.api.auth import provision_user
        from app.models.user import User

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid.jwt.token"
        )

        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # new user
        db.execute = AsyncMock(return_value=mock_result)
        db.refresh = AsyncMock()

        # Minimal Request mock
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"user-agent": "TestAgent/1.0"}

        valid_payload = {
            "sub": "auth0|newuser",
            "email": "new@example.com",
            "email_verified": True,
        }

        # After flush, attach a user_id so audit_service can read it
        uid = uuid.uuid4()

        async def _fake_flush():
            pass

        db.flush = AsyncMock(side_effect=_fake_flush)

        with patch("app.api.auth.verify_token", new=AsyncMock(return_value=valid_payload)), \
             patch("app.services.audit_service.log_auth_event", new=AsyncMock()) as mock_log:
            await provision_user(mock_request, credentials, db)

        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args
        assert call_kwargs.kwargs.get("event_type") == EVENT_PROVISION


class TestDeleteAccountLogsAudit:
    @pytest.mark.asyncio
    async def test_delete_account_logs_deletion_event(self):
        """delete_account must log ACCOUNT_DELETION_REQUESTED."""
        import sys
        from types import ModuleType

        for _mod in ("boto3", "botocore", "botocore.exceptions"):
            if _mod not in sys.modules:
                fake = ModuleType(_mod)
                if _mod == "botocore.exceptions":
                    fake.ClientError = Exception  # type: ignore[attr-defined]
                sys.modules[_mod] = fake

        from fastapi import Request
        from app.api.auth import delete_account
        from app.models.user import User

        user = MagicMock(spec=User)
        user.user_id = uuid.uuid4()
        user.is_active = True
        user.deletion_requested_at = None

        db = _mock_db()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=execute_result)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.2"
        mock_request.headers = {"user-agent": "TestAgent/2.0"}

        with patch("app.workers.health_tasks.purge_user_data") as mock_task, \
             patch("app.services.audit_service.log_auth_event", new=AsyncMock()) as mock_log:
            mock_task.delay = MagicMock()
            await delete_account(mock_request, user, db)

        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args
        event = call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs.get("event_type")
        assert event == EVENT_ACCOUNT_DELETION_REQUESTED
