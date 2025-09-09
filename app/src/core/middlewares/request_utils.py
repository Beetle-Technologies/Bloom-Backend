import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from src.core.constants import DEFAULT_PROXY_COUNT, DEFAULT_PROXY_HEADERS, REQUEST_ID_CTX
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestUtilsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle request utilities such as request ID generation,
    client IP detection, and user agent extraction.\n

    All detected information is stored in request.state for easy access.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        trust_request_id: bool = False,
        request_id_generator: Callable[[], str] = lambda: uuid.uuid4().hex,
        trusted_proxies: list[str] | None = None,
        proxy_count: int | None = None,
        proxy_headers: list[str] | None = None,
    ) -> None:
        super().__init__(app)

        self.request_id_generator = request_id_generator
        self.trust_request_id = trust_request_id

        self.trusted_proxies = trusted_proxies or []
        self.proxy_count = proxy_count or DEFAULT_PROXY_COUNT
        self.proxy_headers = proxy_headers or DEFAULT_PROXY_HEADERS

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = self._get_request_id(request)
        REQUEST_ID_CTX.set(request_id)

        request.state.request_id = request_id
        request.state.client_ip = get_client_ip(
            request,
            proxy_headers=self.proxy_headers,
            trusted_proxies=self.trusted_proxies,
            proxy_count=self.proxy_count,
        )
        request.state.user_agent = self._get_user_agent(request)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            process_time = time.perf_counter() - start_time

            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            logger.error(
                f"{__name__}.dispatch:: Error processing request {request_id} from {request.state.client_ip}: {exc}",
                exc_info=True,
            )
            raise errors.InternalServerError(
                detail="An unexpected error occurred while processing your request."
            ) from exc

    def _get_request_id(self, request: Request) -> str:
        """Extract or generate the request ID."""

        if self.trust_request_id:
            incoming_id = request.headers.get("X-Request-ID")
            if incoming_id and self._validate_request_id(incoming_id):
                return incoming_id
        return self.request_id_generator()

    def _validate_request_id(self, request_id: str) -> bool:
        return len(request_id) <= 200 and all(32 <= ord(c) <= 126 for c in request_id)

    def _get_user_agent(self, request: Request) -> str | None:
        return request.headers.get("User-Agent", None)
