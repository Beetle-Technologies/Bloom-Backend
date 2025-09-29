import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from src.core.constants import DEFAULT_PROXY_COUNT, DEFAULT_PROXY_HEADERS, REQUEST_ID_CTX
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip, get_user_agent
from src.core.logging.config import get_logger
from src.core.logging.filters import add_to_log_context
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = get_logger(__name__)


class RequestUtilsMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for request utilities and comprehensive lifecycle logging.

    This middleware provides:
    - Request ID generation and tracking
    - Client IP detection through proxy headers
    - User agent extraction
    - Comprehensive request lifecycle logging with structured context
    - Performance monitoring and error tracking

    All detected information is stored in request.state for easy access
    and automatically added to the logging context for the entire request.
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
        enable_request_logging: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        super().__init__(app)

        self.request_id_generator = request_id_generator
        self.trust_request_id = trust_request_id
        self.enable_request_logging = enable_request_logging
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

        self.trusted_proxies = trusted_proxies or []
        self.proxy_count = proxy_count or DEFAULT_PROXY_COUNT
        self.proxy_headers = proxy_headers or DEFAULT_PROXY_HEADERS

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process the request with comprehensive logging and context management.

        This method implements the request lifecycle logging pattern:
        1. Log incoming request with context
        2. Process the request
        3. Log outgoing response with outcome and timing
        """
        # Generate or extract request ID
        request_id = self._get_request_id(request)
        REQUEST_ID_CTX.set(request_id)

        # Extract client information
        client_ip = get_client_ip(
            request,
            proxy_headers=self.proxy_headers,
            trusted_proxies=self.trusted_proxies,
            proxy_count=self.proxy_count,
        )
        user_agent = get_user_agent(request)

        # Store in request state for access by other components
        request.state.request_id = request_id
        request.state.client_ip = client_ip
        request.state.user_agent = user_agent

        # Build request context for logging
        request_context = {
            "request_id": request_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params) if request.query_params else None,
        }

        # Add request body to context if enabled (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) < 10000:  # Limit body size for logging
                    request_context["request_body_size"] = len(body)
                    # Don't log actual body content for security reasons by default
            except Exception:
                # If we can't read the body, don't fail the request
                pass

        start_time = time.perf_counter()

        # Use structured logging context for the entire request
        with add_to_log_context(**request_context):
            # Log incoming request
            if self.enable_request_logging:
                logger.info(
                    "Incoming %s request to %s",
                    request.method,
                    request.url.path,
                    extra={
                        "event_type": "request_start",
                        "http_method": request.method,
                        "path": request.url.path,
                        "query_string": (str(request.query_params) if request.query_params else None),
                        "referer": request.headers.get("referer"),
                        "content_type": request.headers.get("content-type"),
                        "content_length": request.headers.get("content-length"),
                    },
                )

            try:
                # Process the request
                response = await call_next(request)

                # Calculate processing time
                process_time = time.perf_counter() - start_time
                duration_ms = process_time * 1000

                # Determine log level based on response status
                log_level = self._get_log_level_for_status(response.status_code)

                # Add timing headers
                response.headers["X-Process-Time"] = f"{process_time:.6f}"
                response.headers["X-Request-ID"] = request_id

                # Log response
                if self.enable_request_logging:
                    extra_data = {
                        "event_type": "request_complete",
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "response_size": response.headers.get("content-length"),
                        "content_type": response.headers.get("content-type"),
                    }

                    # Add response body info if enabled
                    if self.log_response_body:
                        extra_data["response_headers_count"] = len(response.headers)

                    logger.log(
                        log_level,
                        "%s request to %s completed with status %d in %.2fms",
                        request.method,
                        request.url.path,
                        response.status_code,
                        duration_ms,
                        extra=extra_data,
                    )

                return response

            except Exception as exc:
                # Calculate processing time even for errors
                process_time = time.perf_counter() - start_time
                duration_ms = process_time * 1000

                # Log the error with full context
                logger.error(
                    "Request processing failed for %s %s after %.2fms",
                    request.method,
                    request.url.path,
                    duration_ms,
                    exc_info=True,
                    extra={
                        "event_type": "request_error",
                        "duration_ms": duration_ms,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    },
                )

                # Re-raise as internal server error for consistency
                raise errors.InternalServerError(
                    detail="An unexpected error occurred while processing your request."
                ) from exc

    def _get_request_id(self, request: Request) -> str:
        """
        Extract or generate the request ID.

        Args:
            request: The incoming request

        Returns:
            A valid request ID string
        """
        if self.trust_request_id:
            incoming_id = request.headers.get("X-Request-ID")
            if incoming_id and self._validate_request_id(incoming_id):
                return incoming_id
        return self.request_id_generator()

    def _validate_request_id(self, request_id: str) -> bool:
        """
        Validate that a request ID is safe to use.

        Args:
            request_id: The request ID to validate

        Returns:
            True if the request ID is valid and safe
        """
        return (
            len(request_id) <= 200
            and all(32 <= ord(c) <= 126 for c in request_id)
            and request_id.strip() == request_id  # No leading/trailing whitespace
        )

    def _get_log_level_for_status(self, status_code: int) -> int:
        """
        Determine the appropriate log level based on HTTP status code.

        Args:
            status_code: HTTP response status code

        Returns:
            Logging level constant
        """
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        else:
            return logging.INFO
