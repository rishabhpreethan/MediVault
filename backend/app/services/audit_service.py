"""Audit service — write auth events to auth_audit_log (FR-AUTH-009).

No PHI is written here — only user_id (UUID), event_type, IP, and user-agent.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_audit import AuthAuditLog

logger = logging.getLogger(__name__)

# Valid event types
EVENT_LOGIN = "LOGIN"
EVENT_LOGOUT = "LOGOUT"
EVENT_PROVISION = "PROVISION"
EVENT_ACCOUNT_DELETION_REQUESTED = "ACCOUNT_DELETION_REQUESTED"
EVENT_TOKEN_REFRESH = "TOKEN_REFRESH"


async def log_auth_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write an auth event to auth_audit_log.

    Never raises — swallows all errors so audit failures never break
    the main request path.
    """
    try:
        entry = AuthAuditLog(
            log_id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        await db.flush()
    except Exception:  # noqa: BLE001
        logger.warning("audit log write failed for event_type=%s user_id=%s", event_type, user_id)
