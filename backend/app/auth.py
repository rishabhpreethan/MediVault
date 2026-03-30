"""Auth0 JWT verification (MV-011)."""
from __future__ import annotations

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.config import settings

_jwks_cache: dict | None = None


async def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{settings.auth0_domain}/.well-known/jwks.json"
            )
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


def _find_rsa_key(jwks: dict, kid: str) -> dict | None:  # type: ignore[valid-type]
    """Return the JWK matching the given key ID, or None."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key.get("use"),
                "n": key["n"],
                "e": key["e"],
            }
    return None


async def verify_token(token: str) -> dict:
    """Verify an Auth0 RS256 JWT and return its claims.

    Raises:
        JWTError: on any validation failure (expired, bad sig, wrong aud/iss, etc.)
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise JWTError(f"Invalid token header: {exc}") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Token header missing 'kid'")

    jwks = await get_jwks()
    rsa_key = _find_rsa_key(jwks, kid)

    if rsa_key is None:
        # Key may have rotated — bust cache and retry once
        global _jwks_cache
        _jwks_cache = None
        jwks = await get_jwks()
        rsa_key = _find_rsa_key(jwks, kid)

    if rsa_key is None:
        raise JWTError(f"Unable to find signing key for kid={kid!r}")

    issuer = f"https://{settings.auth0_domain}/"

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=issuer,
        )
    except ExpiredSignatureError as exc:
        raise JWTError("Token has expired") from exc
    except JWTError:
        raise

    return payload
