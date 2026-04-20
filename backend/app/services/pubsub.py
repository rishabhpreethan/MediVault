"""Redis pub/sub helpers for real-time family circle updates (MV-164).

Publishing: call publish_family_updated(user_id) after any mutation that
changes a user's family circle view (invite accept/decline, grant, revoke).

Subscribing: the SSE endpoint uses subscribe_family_updates(user_id) to
stream events to the browser as long as the connection stays open.
"""
import asyncio
import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_CHANNEL_PREFIX = "family"


def _channel(user_id: str) -> str:
    return f"{_CHANNEL_PREFIX}:{user_id}"


async def publish_family_updated(user_id: str) -> None:
    """Publish a family-updated event to the given user's channel."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await r.publish(_channel(user_id), "family-updated")
    except Exception:
        logger.warning("pubsub_publish_failed", extra={"user_id": user_id})
    finally:
        await r.aclose()


async def subscribe_family_updates(user_id: str):
    """Async generator yielding SSE-formatted strings for the given user.

    Yields a keepalive comment every 25 s so proxies don't close idle
    connections, and a data event whenever the family circle changes.
    Intended to be consumed by a FastAPI StreamingResponse.
    """
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(_channel(user_id))
    try:
        while True:
            # Non-blocking check with a short timeout so we can interleave keepalives
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                yield "data: family-updated\n\n"
            else:
                # Yield keepalive every ~25 s to prevent proxy timeouts
                await asyncio.sleep(25)
                yield ": keepalive\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(_channel(user_id))
        await r.aclose()
