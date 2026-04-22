"""One-time script to delete all existing notifications from the database.

Usage (from backend/ directory):
    python3 scripts/clear_notifications.py

Or via Docker:
    docker exec -it medivault-api python scripts/clear_notifications.py
"""
import asyncio
from sqlalchemy import text
from app.database import async_session_factory


async def main() -> None:
    async with async_session_factory() as session:
        result = await session.execute(text("DELETE FROM notifications"))
        await session.commit()
        print(f"Deleted {result.rowcount} notification(s).")


if __name__ == "__main__":
    asyncio.run(main())
