import logging
import time
from typing import Callable

from fastapi import Request, Response, status
from src.core.config import settings
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip
from src.libs.throttler import limiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestThrottlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to incoming requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        namespace: str | None = None,
        custom_limit: str | None = None,
        key_func: Callable[[Request], str] | None = None,
    ) -> None:
        super().__init__(app)
        self.namespace = namespace or settings.RATE_LIMIT_NAMESPACE
        self.custom_limit = custom_limit
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        client_ip = get_client_ip(request)
        return client_ip or "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        client_key = self.key_func(request)

        try:
            allowed = await limiter.hit(
                namespace=self.namespace,
                client_key=client_key,
                custom_limit=self.custom_limit,
            )

            if not allowed:
                stats, limit_amount = await limiter.get_window_stats_with_limit(
                    namespace=self.namespace,
                    client_key=client_key,
                    custom_limit=self.custom_limit,
                )

                current_time = time.time()
                retry_after = max(1, int(stats.reset_time - current_time))

                logger.warning(
                    f"Rate limit exceeded for client {client_key} in namespace {self.namespace}. "
                    f"Reset time: {stats.reset_time}"
                )

                response = Response(
                    content=errors.RateLimitExceededError().marshal(),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/problem+json",
                )

                response.headers["X-RateLimit-Limit"] = str(limit_amount)
                response.headers["X-RateLimit-Remaining"] = str(stats.remaining)
                response.headers["X-RateLimit-Reset"] = str(int(stats.reset_time))
                response.headers["Retry-After"] = str(retry_after)

                return response

            response = await call_next(request)

            stats, limit_amount = await limiter.get_window_stats_with_limit(
                namespace=self.namespace,
                client_key=client_key,
                custom_limit=self.custom_limit,
            )

            response.headers["X-RateLimit-Limit"] = str(limit_amount)
            response.headers["X-RateLimit-Remaining"] = str(stats.remaining)
            response.headers["X-RateLimit-Reset"] = str(int(stats.reset_time))

            return response

        except Exception as e:
            logger.error(f"Error in request throttler middleware: {e}")
            return await call_next(request)
