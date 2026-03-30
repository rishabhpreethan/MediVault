from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_token

security = HTTPBearer()

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DbSession,
):
    """Validate Auth0 JWT and return the authenticated user. Implemented in MV-011."""
    # Full implementation in MV-011 — stub raises until then
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth middleware implemented in MV-011",
    )


CurrentUser = Annotated[object, Depends(get_current_user)]


def require_member_access(member_id: UUID, current_user) -> None:
    """Verify the current user owns the requested family member. Implemented in MV-011."""
    pass
