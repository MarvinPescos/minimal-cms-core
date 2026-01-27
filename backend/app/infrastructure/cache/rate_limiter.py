"""
Rate limiting configuration using SlowAPI with Redis backend.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from .redis_client import get_redis_url

#
def get_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses authenticated user ID if available, otherwise falls back to IP.
    """
    if hasattr(request.state, "user") and request.state.user:
        return str(request.state.user.user_id)
    
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_identifier,
    storage_uri=get_redis_url(),
    default_limits=["100/minute"] 
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "RateLimitExceeded",
            "message": "Too many requests. Please slow down.",
            "details": {
                "retry_after": exc.detail
            }
        }
    )


class RateLimits:
    """Common rate limit configurations."""
    AUTH_STRICT = "5/minute"      # Signup, login  
    AUTH_MEDIUM = "10/minute"     # Sign in attempts
    PASSWORD = "3/minute"         # Password reset requests
    STANDARD = "100/minute"       # General API endpoints
    READ_HEAVY = "200/minute"     # Read-only endpoints
