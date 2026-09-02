"""Redis connection management."""
from typing import Optional

import redis.asyncio as redis_async
from loguru import logger

from app.config import settings

# Async Redis client (lazy initialization)
_async_redis: Optional[redis_async.Redis] = None


def get_async_redis() -> redis_async.Redis:
    """Get or create the async Redis client singleton.

    Returns:
        Async Redis client instance.
    """
    global _async_redis
    if _async_redis is None:
        _async_redis = redis_async.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info(f"Async Redis client initialized: {settings.REDIS_URL}")
    return _async_redis


async def redis_ping() -> bool:
    """Test Redis connection.

    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        client = get_async_redis()
        return await client.ping()
    except Exception as e:
        logger.error(f"Redis ping failed: {e}")
        return False


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _async_redis
    if _async_redis is not None:
        await _async_redis.close()
        _async_redis = None
        logger.info("Redis connection closed")
