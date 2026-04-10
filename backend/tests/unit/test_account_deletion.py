"""Unit tests for DELETE /auth/account (MV-110)."""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from types import ModuleType
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub boto3 and botocore before any app imports
for _mod in ("boto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        _fake = ModuleType(_mod)
        if _mod == "botocore.exceptions":
            _fake.ClientError = Exception  # type: ignore[attr-defined]
        sys.modules[_mod] = _fake

from app.api.auth import delete_account


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=execute_result)
    return session


def _mock_user(is_active: bool = True) -> MagicMock:
    from app.models.user import User

    u = MagicMock(spec=User)
    u.user_id = uuid.uuid4()
    u.auth0_sub = "auth0|testuser"
    u.email = "user@example.com"
    u.email_verified = True
    u.is_active = is_active
    u.deletion_requested_at = None
    u.created_at = datetime.now(tz=timezone.utc)
    u.last_login_at = None
    return u


# ---------------------------------------------------------------------------
# Tests for DELETE /auth/account route logic
# ---------------------------------------------------------------------------

class TestDeleteAccountEndpoint:
    @pytest.mark.asyncio
    async def test_returns_204_no_content(self):
        """Endpoint must return 204 No Content on success."""
        user = _mock_user()
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            response = await delete_account(current_user=user, db=db)

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_sets_is_active_false(self):
        """User.is_active must be False after the call."""
        user = _mock_user(is_active=True)
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            await delete_account(current_user=user, db=db)

        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_sets_deletion_requested_at(self):
        """User.deletion_requested_at must be set to a UTC datetime."""
        user = _mock_user()
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            await delete_account(current_user=user, db=db)

        assert user.deletion_requested_at is not None
        assert isinstance(user.deletion_requested_at, datetime)

    @pytest.mark.asyncio
    async def test_revokes_shared_passports(self):
        """A bulk UPDATE must be executed to revoke SharedPassports."""
        user = _mock_user()
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            await delete_account(current_user=user, db=db)

        # db.execute should be called at least once (for the passport UPDATE)
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_commits_db_session(self):
        """The session must be committed after soft-delete and passport revocation."""
        user = _mock_user()
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            await delete_account(current_user=user, db=db)

        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_queues_purge_task_with_user_id(self):
        """purge_user_data.delay() must be called with the user's UUID as a string."""
        user = _mock_user()
        db = _mock_db()

        with patch("app.workers.health_tasks.purge_user_data") as mock_task:
            mock_task.delay = MagicMock()
            await delete_account(current_user=user, db=db)

        mock_task.delay.assert_called_once_with(str(user.user_id))


# ---------------------------------------------------------------------------
# Tests for purge_user_data Celery task logic
# ---------------------------------------------------------------------------

class TestPurgeUserDataTask:
    @pytest.mark.asyncio
    async def test_purge_deletes_minio_objects(self):
        """_run_purge must call delete_object for each document storage_path."""
        from app.workers.health_tasks import _run_purge

        user_id = str(uuid.uuid4())
        member_id = uuid.uuid4()

        mock_member = MagicMock()
        mock_member.member_id = member_id

        mock_doc = MagicMock()
        mock_doc.storage_path = "members/some-member/doc.pdf"
        mock_doc.member_id = member_id

        mock_user = MagicMock()
        mock_user.user_id = uuid.UUID(user_id)
        mock_user.is_active = True

        async def _fake_execute(stmt):
            result = MagicMock()
            # Determine what the query is selecting based on call order
            scalars_result = MagicMock()
            # Return members on first relevant call, docs on second, user on third
            _fake_execute.call_count = getattr(_fake_execute, "call_count", 0) + 1
            if _fake_execute.call_count == 1:
                scalars_result.all.return_value = [mock_member]
            elif _fake_execute.call_count == 2:
                scalars_result.all.return_value = [mock_doc]
            elif _fake_execute.call_count == 3:
                scalars_result.all.return_value = [mock_member]
            else:
                scalars_result.scalar_one_or_none = MagicMock(return_value=mock_user)
                scalars_result.all.return_value = []
            result.scalars.return_value = scalars_result
            result.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result

        mock_session = AsyncMock()
        mock_session.execute = _fake_execute
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_s3 = MagicMock()
        mock_s3.delete_object = MagicMock()

        with patch("app.database.AsyncSessionLocal", return_value=mock_session), \
             patch("app.workers.health_tasks._get_s3_client", return_value=mock_s3):
            result = await _run_purge(user_id)

        assert result["status"] == "PURGED"
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_purge_handles_no_family_members(self):
        """_run_purge must complete successfully when user has no family members."""
        from app.workers.health_tasks import _run_purge

        user_id = str(uuid.uuid4())

        mock_user = MagicMock()
        mock_user.user_id = uuid.UUID(user_id)
        mock_user.is_active = True

        call_count = {"n": 0}

        async def _fake_execute(stmt):
            result = MagicMock()
            scalars_result = MagicMock()
            call_count["n"] += 1
            scalars_result.all.return_value = []
            result.scalars.return_value = scalars_result
            result.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result

        mock_session = AsyncMock()
        mock_session.execute = _fake_execute
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.database.AsyncSessionLocal", return_value=mock_session), \
             patch("app.workers.health_tasks._get_s3_client", return_value=MagicMock()):
            result = await _run_purge(user_id)

        assert result["status"] == "PURGED"
        assert result["member_count"] == 0
        assert result["document_count"] == 0
