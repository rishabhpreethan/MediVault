"""Notification dispatch service — creates and persists in-app Notification rows."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

logger = logging.getLogger(__name__)


async def dispatch_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Notification:
    """Create and persist an in-app notification for *user_id*.

    Never include PHI in *title*, *body*, or *metadata* — only IDs, status
    tokens, and event names.

    Returns the newly committed Notification row.
    """
    notification = Notification(
        notification_id=uuid.uuid4(),
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        action_url=action_url,
        extra_data=metadata,
    )
    db.add(notification)
    await db.flush()  # write within the caller's transaction; caller commits

    logger.info(
        "notification_dispatched",
        extra={
            "notification_id": str(notification.notification_id),
            "user_id": str(user_id),
            "type": type,
        },
    )
    return notification
