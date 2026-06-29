"""Health check helpers."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def check_database() -> tuple[bool, str]:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def check_redis() -> tuple[bool, str]:
    try:
        import redis

        from app.core.config import settings

        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)
