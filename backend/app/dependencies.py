from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.family_member import FamilyMember  # noqa: TC002 — used at runtime

security = HTTPBearer()

DbSession = Annotated[AsyncSession, Depends(get_db)]

DEV_SUPERUSER_SUB = "dev|superuser"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DbSession,
) -> User:
    """Validate Auth0 JWT and return the authenticated User row.

    In development mode, a static dev token bypasses Auth0 and returns the
    seeded superuser directly — never active in production.

    Raises:
        401 if the token is missing, malformed, expired, or has wrong audience/issuer.
        404 if the sub claim doesn't match any User record (user not provisioned yet).
    """
    # Dev bypass — only when environment=development and token is configured
    if (
        settings.environment == "development"
        and settings.dev_superuser_token
        and credentials.credentials == settings.dev_superuser_token
    ):
        result = await db.execute(select(User).where(User.auth0_sub == DEV_SUPERUSER_SUB))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dev superuser not found — run scripts/seed_dev.py first",
            )
        return user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = await verify_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    sub: str | None = payload.get("sub")
    if not sub:
        raise credentials_exception

    result = await db.execute(select(User).where(User.auth0_sub == sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not provisioned — call /auth/provision first",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_vault_access(
    member_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Verify that *current_user* is permitted to access *member_id*'s vault.

    Two access paths are allowed:
    1. **Owner** — the FamilyMember's user_id equals current_user.user_id.
    2. **Delegate** — a VaultAccessGrant exists where
       grantee_user_id == current_user.user_id AND
       target_user_id  == the member's owning user_id.

    Raises:
        404 if the FamilyMember row does not exist.
        403 if neither owner nor delegate access applies.
    """
    from app.models.family_circle import VaultAccessGrant  # noqa: PLC0415 — avoids circular import

    # Load the member
    member_result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == member_id)
    )
    member = member_result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )

    # Path 1 — owner
    if member.user_id == current_user.user_id:
        return

    # Path 2 — delegate via VaultAccessGrant
    target_user_id = member.user_id
    grant_result = await db.execute(
        select(VaultAccessGrant).where(
            VaultAccessGrant.grantee_user_id == current_user.user_id,
            VaultAccessGrant.target_user_id == target_user_id,
        )
    )
    if grant_result.scalar_one_or_none() is not None:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
    )


def require_member_access(member_id: UUID, current_user: User) -> None:
    """Verify that current_user owns the requested family member.

    Raises:
        403 if the member does not belong to the current user.
    """
    # member_id is checked against the current_user's family members.
    # The actual DB lookup happens in the route; this guard is called after
    # the FamilyMember is loaded to confirm ownership.
    # Routes pass the already-loaded FamilyMember's user_id for comparison.
    # This function accepts the UUID of the member being requested and raises
    # if it is not owned by current_user. Routes should call:
    #   require_member_access(member.user_id, current_user)
    # where member.user_id is the FK back to users.user_id.
    if member_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
