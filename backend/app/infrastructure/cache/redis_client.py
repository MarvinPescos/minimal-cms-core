"""
Redis client for caching and rate limiting storage.
"""
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from app.core import settings
from app.infrastructure.observability.logging_setup import log


def get_redis_url() -> str:
    """Build Redis URL from settings."""
    # Handle docker-compose style port mapping (e.g., "6379:6379")
    port = settings.REDIS_PORT.split(":")[0] if ":" in settings.REDIS_PORT else settings.REDIS_PORT
    return f"redis://{settings.REDIS_HOST}:{port}"

    # try:
    #     int(port)
    # except:
    #     raise ValueError(f"Invalid REDIS_PORT: {settings.REDIS_PORT}")
    

    # if hasattr(settings, "REDIS_PASSWORD")


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
