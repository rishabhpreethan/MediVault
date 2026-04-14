"""Auth routes — user provisioning (MV-013) and account deletion (MV-110)."""
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.database import get_db
from app.dependencies import CurrentUser
from app.limiter import limiter
from app.models.family_member import FamilyMember
from app.models.passport import SharedPassport
from app.models.user import User

router = APIRouter()
_bearer = HTTPBearer()

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    user_id: uuid.UUID
    auth0_sub: str
    email: Optional[str] = None
    email_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /auth/provision
# ---------------------------------------------------------------------------

@router.post("/provision", response_model=UserResponse, status_code=200)
async def provision_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: DbSession,
) -> User:
    """Upsert a User row from the validated Auth0 JWT claims.

    Idempotent — safe to call on every login. Creates the user on first call,
    updates email/email_verified/last_login_at on subsequent calls.

    Auth0 claims used:
      - sub           → auth0_sub (PK lookup)
      - email         → email
      - email_verified → email_verified
    """
    from app.services import audit_service  # noqa: PLC0415
    try:
        payload = await verify_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub: str = payload.get("sub", "")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub claim")

    email: Optional[str] = payload.get("email")
    email_verified: bool = bool(payload.get("email_verified", False))

    result = await db.execute(select(User).where(User.auth0_sub == sub))
    user = result.scalar_one_or_none()

    now = datetime.now(tz=timezone.utc)

    ip_address: Optional[str] = request.client.host if request.client else None
    user_agent_header: Optional[str] = request.headers.get("user-agent")

    if user is None:
        user = User(
            auth0_sub=sub,
            email=email,
            email_verified=email_verified,
            last_login_at=now,
        )
        db.add(user)
        await db.flush()

        # Create the self FamilyMember so the user can upload documents immediately
        # (documents are scoped to a member_id — without this, a fresh user has none).
        display_name = (email or "").split("@")[0].replace(".", " ").title() or "Me"
        self_member = FamilyMember(
            user_id=user.user_id,
            full_name=display_name,
            relationship="SELF",
            is_self=True,
        )
        db.add(self_member)

        await audit_service.log_auth_event(
            db,
            event_type=audit_service.EVENT_PROVISION,
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent_header,
        )
    else:
        user.email = email
        user.email_verified = email_verified
        user.last_login_at = now

        # Backfill self-member for existing users who pre-date this fix.
        existing_self = await db.execute(
            select(FamilyMember).where(
                FamilyMember.user_id == user.user_id,
                FamilyMember.is_self == True,  # noqa: E712
            )
        )
        if existing_self.scalar_one_or_none() is None:
            display_name = (email or "").split("@")[0].replace(".", " ").title() or "Me"
            db.add(FamilyMember(
                user_id=user.user_id,
                full_name=display_name,
                relationship="SELF",
                is_self=True,
            ))

        await audit_service.log_auth_event(
            db,
            event_type=audit_service.EVENT_LOGIN,
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent_header,
        )

    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# DELETE /auth/account
# ---------------------------------------------------------------------------

@router.delete("/account", response_model=None, status_code=204)
async def delete_account(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    """Soft-delete the authenticated user's account and queue async data purge.

    1. Marks the user as inactive and records deletion_requested_at.
    2. Revokes all SharedPassports belonging to the user.
    3. Enqueues the ``purge_user_data`` Celery task to hard-delete all data
       and MinIO objects asynchronously.

    Returns 204 No Content.
    """
    from app.services import audit_service  # noqa: PLC0415
    from app.workers.health_tasks import purge_user_data  # noqa: PLC0415

    now = datetime.now(tz=timezone.utc)
    user_id_str = str(current_user.user_id)
    ip_address: Optional[str] = request.client.host if request.client else None
    user_agent_header: Optional[str] = request.headers.get("user-agent")

    # 1. Soft-delete the user
    current_user.is_active = False
    current_user.deletion_requested_at = now

    # 2. Revoke all SharedPassports for this user
    await db.execute(
        update(SharedPassport)
        .where(SharedPassport.user_id == current_user.user_id)
        .values(is_active=False)
    )

    # 3. Audit log the deletion request
    await audit_service.log_auth_event(
        db,
        event_type=audit_service.EVENT_ACCOUNT_DELETION_REQUESTED,
        user_id=current_user.user_id,
        ip_address=ip_address,
        user_agent=user_agent_header,
    )

    await db.commit()

    # 4. Queue async purge task
    purge_user_data.delay(user_id_str)

    return Response(status_code=204)
