"""
Redis client for caching and rate limiting storage.
"""
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from app.core import settings
from app.infrastructure.observability.logging_setup import log


def get_redis_url() -> str:
    """Get Redis URL from settings.
    
    Supports both standard redis:// and Upstash rediss:// URLs.
    """
    return settings.REDIS_URL


# Async Redis client for use with rate limiting
redis_client = redis.from_url(
    get_redis_url(),
    encoding="utf-8",
    decode_responses=True
)


async def check_redis_connection() -> bool:
    """Check if Redis is reachable."""
    try:
        await redis_client.ping()
        return True
    except redis.ConnectionError:
        return False
