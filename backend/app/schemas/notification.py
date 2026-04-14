"""Pydantic v2 schemas for the Notifications API."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str
    is_read: bool
    action_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    limit: int
