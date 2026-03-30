"""Auth0 JWT verification. Full implementation in MV-011."""
import httpx
from jose import JWTError, jwt

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


async def verify_token(token: str) -> dict:
    """Verify an Auth0 RS256 JWT and return its claims. Full implementation in MV-011."""
    raise NotImplementedError("Implemented in MV-011")
