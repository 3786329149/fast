from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import get_settings

redis_client: Redis | None = None


async def init_redis() -> None:
    global redis_client
    settings = get_settings()
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
