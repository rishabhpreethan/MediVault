"""Unit tests for POST /auth/provision logic (MV-013)."""
import sys
from types import ModuleType
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

for _mod in ("boto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        _fake = ModuleType(_mod)
        if _mod == "botocore.exceptions":
            _fake.ClientError = Exception  # type: ignore[attr-defined]
        sys.modules[_mod] = _fake

from app.api.auth import provision_user, UserResponse

_MOCK_REQUEST = MagicMock(spec=Request)
_MOCK_REQUEST.client = MagicMock()
_MOCK_REQUEST.client.host = "127.0.0.1"
_MOCK_REQUEST.headers = {}


def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(sub="auth0|test", email="user@example.com", email_verified=True):
    from app.models.user import User
    u = MagicMock(spec=User)
    u.user_id = uuid.uuid4()
    u.auth0_sub = sub
    u.email = email
    u.email_verified = email_verified
    u.is_active = True
    u.created_at = datetime.now(tz=timezone.utc)
    u.last_login_at = None
    return u


_VALID_PAYLOAD = {
    "sub": "auth0|test",
    "email": "user@example.com",
    "email_verified": True,
}

_CREDENTIALS = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")


class TestProvisionLogic:
    @pytest.mark.asyncio
    async def test_creates_user_when_not_exists(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.auth.verify_token", new=AsyncMock(return_value=_VALID_PAYLOAD)):
            # After refresh, simulate the created user being returned
            created_user = _mock_user()
            db.refresh = AsyncMock(side_effect=lambda u: None)

            # After refresh, simulate the created user being returned
            await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        from app.models.user import User
        user_adds = [c for c in db.add.call_args_list if isinstance(c.args[0], User)]
        assert len(user_adds) == 1, "db.add must be called once with a User"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_user_on_second_call(self):
        existing_user = _mock_user()
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.auth.verify_token", new=AsyncMock(return_value=_VALID_PAYLOAD)):
            await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        # update path: User should NOT be added (only audit log may be added)
        from app.models.user import User
        user_adds = [c for c in db.add.call_args_list if isinstance(c.args[0], User)]
        assert len(user_adds) == 0, "db.add should not be called with User on update path"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_last_login_at_on_each_call(self):
        existing_user = _mock_user()
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.auth.verify_token", new=AsyncMock(return_value=_VALID_PAYLOAD)):
            await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        assert existing_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_raises_401_on_invalid_token(self):
        from jose import JWTError
        db = _mock_db()

        with patch("app.api.auth.verify_token", new=AsyncMock(side_effect=JWTError("bad token"))):
            with pytest.raises(HTTPException) as exc_info:
                await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_when_sub_missing(self):
        db = _mock_db()

        with patch("app.api.auth.verify_token", new=AsyncMock(return_value={"email": "x@y.com"})):
            with pytest.raises(HTTPException) as exc_info:
                await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_uses_email_from_token(self):
        existing_user = _mock_user(email="old@example.com")
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        db.execute = AsyncMock(return_value=mock_result)

        payload = {**_VALID_PAYLOAD, "email": "new@example.com"}
        with patch("app.api.auth.verify_token", new=AsyncMock(return_value=payload)):
            await provision_user(_MOCK_REQUEST, _CREDENTIALS, db)

        assert existing_user.email == "new@example.com"


class TestUserResponseSchema:
    def test_user_response_fields(self):
        user = _mock_user()
        # Verify the schema has all expected fields
        fields = set(UserResponse.model_fields.keys())
        assert "user_id" in fields
        assert "auth0_sub" in fields
        assert "email" in fields
        assert "email_verified" in fields
        assert "is_active" in fields
        assert "created_at" in fields

    def test_email_is_optional(self):
        from pydantic import TypeAdapter
        from typing import Optional
        field = UserResponse.model_fields["email"]
        assert not field.is_required()
