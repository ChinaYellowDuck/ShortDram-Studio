"""Quick connection verification test."""
import asyncio

import pytest
from sqlalchemy import create_engine, text

from app.config import settings


def test_postgres_connection():
    """Verify PostgreSQL connection works."""
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_redis_connection():
    """Verify Redis connection works."""
    import redis.asyncio as redis_async

    client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        result = await client.ping()
        assert result is True
    finally:
        await client.close()
