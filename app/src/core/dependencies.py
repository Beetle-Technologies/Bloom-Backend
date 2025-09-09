import time
from functools import lru_cache
from types import CoroutineType
from typing import Any, Callable

from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from multidict import CIMultiDict
from src.core.config import settings
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip, parse_bloom_client_header
from src.core.types import BloomClientInfo
from src.libs.throttler import limiter


@lru_cache(maxsize=1)
def get_security_schemes() -> tuple[HTTPBearer, OAuth2PasswordBearer]:
    return (
        HTTPBearer(),
        OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login"),
    )


def create_rate_limit_dependency(
    namespace: str,
    custom_limit: str | None = None,
    key_func: Callable[[Request], str] | None = None,
) -> Callable[..., CoroutineType[Any, Any, None]]:
    """
    Create a rate limit dependency for specific routes or routers.

    Args:
        namespace (str): The namespace for rate limiting (e.g., "auth", "api", "uploads")
        custom_limit (str | None): Optional custom limit string (e.g., "10/minute", "100/hour")
        key_func (Callable[[Request], str] | None): Optional function to extract client key from request

    Returns:
        Dependency function that can be used with FastAPI routes
    """

    def _default_key_func(request: Request) -> str:
        """Default function to generate client key from request"""
        client_ip = get_client_ip(request)
        return client_ip or "unknown"

    async def rate_limit_dependency(request: Request) -> None:
        """Rate limit dependency function"""
        client_key_func = key_func or _default_key_func
        client_key = client_key_func(request)

        allowed = await limiter.hit(
            namespace=namespace,
            client_key=client_key,
            custom_limit=custom_limit,
        )

        if not allowed:
            stats, limit_amount = await limiter.get_window_stats_with_limit(
                namespace=namespace,
                client_key=client_key,
                custom_limit=custom_limit,
            )

            current_time = time.time()
            retry_after = max(1, int(stats.reset_time - current_time))

            raise errors.RateLimitExceededError(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=CIMultiDict(
                    {
                        "X-RateLimit-Limit": str(limit_amount),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(stats.reset_time)),
                        "Retry-After": str(retry_after),
                    }
                ),
            )

    return rate_limit_dependency


def validate_bloom_client_header(
    request: Request, x_bloom_client: str = Header(None, alias="X-Bloom-Client")
) -> BloomClientInfo:
    """
    Validate and parse the X-Bloom-Client header.
    For OpenAPI docs endpoints, provides a default header value.

    Args:
        request (Request): The FastAPI request object
        x_bloom_client (str): The X-Bloom-Client header value

    Returns:
        BloomClientInfo: Parsed client information
    """
    openapi_paths = [settings.OPENAPI_DOCS_URL, settings.OPENAPI_JSON_SCHEMA_URL]
    if request.url.path in openapi_paths:
        default_header = "platform=web; version=1.0.0; app=bloom-main"
        return parse_bloom_client_header(default_header)

    if not x_bloom_client:
        raise errors.InvalidClientHeaderError(detail="X-Bloom-Client header is required")

    return parse_bloom_client_header(x_bloom_client)


auth_rate_limit = Depends(create_rate_limit_dependency("bloom_auth", "10/minute"))
api_rate_limit = Depends(create_rate_limit_dependency("bloom_api", "100/minute"))
upload_rate_limit = Depends(create_rate_limit_dependency("bloom_uploads", "5/minute"))
strict_rate_limit = Depends(create_rate_limit_dependency("bloom_strict", "5/minute"))
per_minute_rate_limit = Depends(create_rate_limit_dependency("bloom_per_minute", "1/minute"))
is_bloom_client = Depends(validate_bloom_client_header)
