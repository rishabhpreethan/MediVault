"""Notifications API — MV-131."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, update

from app.dependencies import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationResponse,
    PaginatedNotificationsResponse,
    UnreadCountResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _notification_to_response(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        notification_id=n.notification_id,
        user_id=n.user_id,
        type=n.type,
        title=n.title,
        body=n.body,
        is_read=n.is_read,
        action_url=n.action_url,
        metadata=n.metadata,
        created_at=n.created_at,
    )


# ---------------------------------------------------------------------------
# GET /notifications
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedNotificationsResponse)
async def list_notifications(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedNotificationsResponse:
    """Return paginated notifications for the current user, newest first."""
    offset = (page - 1) * limit

    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.user_id
        )
    )
    total = count_result.scalar_one()

    items_result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = [_notification_to_response(n) for n in items_result.scalars().all()]

    return PaginatedNotificationsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /notifications/unread-count
# ---------------------------------------------------------------------------


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: CurrentUser,
    db: DbSession,
) -> UnreadCountResponse:
    """Return the number of unread notifications for the current user."""
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    count = result.scalar_one()
    return UnreadCountResponse(count=count)


# ---------------------------------------------------------------------------
# PATCH /notifications/{notification_id}/read
# ---------------------------------------------------------------------------


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> NotificationResponse:
    """Mark a single notification as read (ownership verified)."""
    result = await db.execute(
        select(Notification).where(Notification.notification_id == notification_id)
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Notification not found"},
        )
    if notif.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Access denied"},
        )

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)

    logger.info(
        "notification_marked_read",
        extra={
            "notification_id": str(notification_id),
            "user_id": str(current_user.user_id),
        },
    )
    return _notification_to_response(notif)


# ---------------------------------------------------------------------------
# POST /notifications/read-all
# ---------------------------------------------------------------------------


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def mark_all_read(
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Mark all notifications as read for the current user."""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()
    logger.info(
        "all_notifications_marked_read",
        extra={"user_id": str(current_user.user_id)},
    )


# ---------------------------------------------------------------------------
# DELETE /notifications/{notification_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a notification (ownership verified)."""
    result = await db.execute(
        select(Notification).where(Notification.notification_id == notification_id)
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Notification not found"},
        )
    if notif.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Access denied"},
        )

    await db.delete(notif)
    await db.commit()
    logger.info(
        "notification_deleted",
        extra={
            "notification_id": str(notification_id),
            "user_id": str(current_user.user_id),
        },
    )
