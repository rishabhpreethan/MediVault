"""Unit tests for Auth0 JWT verification (MV-011)."""
from unittest.mock import AsyncMock, patch

import pytest
from jose import JWTError

from app.auth import _find_rsa_key, verify_token

# ---------------------------------------------------------------------------
# Fixtures / constants
# ---------------------------------------------------------------------------

_SAMPLE_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "abc123",
            "use": "sig",
            "n": "some-n-value",
            "e": "AQAB",
        }
    ]
}

_SAMPLE_PAYLOAD = {"sub": "auth0|user123", "email": "user@example.com"}


# ---------------------------------------------------------------------------
# _find_rsa_key
# ---------------------------------------------------------------------------

class TestFindRsaKey:
    def test_returns_key_when_kid_matches(self):
        key = _find_rsa_key(_SAMPLE_JWKS, "abc123")
        assert key is not None
        assert key["kid"] == "abc123"
        assert key["kty"] == "RSA"

    def test_returns_none_when_kid_not_found(self):
        key = _find_rsa_key(_SAMPLE_JWKS, "nonexistent")
        assert key is None

    def test_returns_none_for_empty_jwks(self):
        assert _find_rsa_key({"keys": []}, "abc123") is None

    def test_returned_key_has_required_fields(self):
        key = _find_rsa_key(_SAMPLE_JWKS, "abc123")
        for field in ("kty", "kid", "n", "e"):
            assert field in key


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------

class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_raises_jwt_error_on_bad_header(self):
        with pytest.raises(JWTError):
            await verify_token("not.a.jwt")

    @pytest.mark.asyncio
    async def test_raises_jwt_error_when_kid_missing(self):
        import jose.jwt as _jwt
        # Build a token with no kid in header
        with patch("app.auth.jwt.get_unverified_header", return_value={}):
            with pytest.raises(JWTError, match="missing 'kid'"):
                await verify_token("dummy.token.value")

    @pytest.mark.asyncio
    async def test_raises_when_key_not_found_in_jwks(self):
        with patch("app.auth.jwt.get_unverified_header", return_value={"kid": "unknown"}), \
             patch("app.auth.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with pytest.raises(JWTError, match="Unable to find signing key"):
                await verify_token("any.token.here")

    @pytest.mark.asyncio
    async def test_retries_jwks_on_unknown_kid(self):
        """If kid not found, cache is busted and JWKS fetched again."""
        get_jwks_mock = AsyncMock(return_value={"keys": []})
        with patch("app.auth.jwt.get_unverified_header", return_value={"kid": "missing"}), \
             patch("app.auth.get_jwks", get_jwks_mock):
            with pytest.raises(JWTError):
                await verify_token("any.token.here")
        assert get_jwks_mock.call_count == 2  # initial fetch + retry after cache bust

    @pytest.mark.asyncio
    async def test_returns_payload_on_valid_token(self):
        rsa_key = {
            "kty": "RSA", "kid": "abc123", "use": "sig",
            "n": "some-n-value", "e": "AQAB",
        }
        with patch("app.auth.jwt.get_unverified_header", return_value={"kid": "abc123"}), \
             patch("app.auth.get_jwks", new=AsyncMock(return_value=_SAMPLE_JWKS)), \
             patch("app.auth.jwt.decode", return_value=_SAMPLE_PAYLOAD):
            payload = await verify_token("valid.jwt.token")
        assert payload["sub"] == "auth0|user123"

    @pytest.mark.asyncio
    async def test_raises_on_expired_token(self):
        from jose.exceptions import ExpiredSignatureError
        with patch("app.auth.jwt.get_unverified_header", return_value={"kid": "abc123"}), \
             patch("app.auth.get_jwks", new=AsyncMock(return_value=_SAMPLE_JWKS)), \
             patch("app.auth.jwt.decode", side_effect=ExpiredSignatureError("expired")):
            with pytest.raises(JWTError, match="expired"):
                await verify_token("expired.jwt.token")

    @pytest.mark.asyncio
    async def test_raises_on_wrong_audience(self):
        with patch("app.auth.jwt.get_unverified_header", return_value={"kid": "abc123"}), \
             patch("app.auth.get_jwks", new=AsyncMock(return_value=_SAMPLE_JWKS)), \
             patch("app.auth.jwt.decode", side_effect=JWTError("Invalid audience")):
            with pytest.raises(JWTError):
                await verify_token("wrong.audience.token")
