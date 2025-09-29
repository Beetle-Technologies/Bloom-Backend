import logging
import sys
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from src.core.logging.filters import get_log_context

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with structured logging.

    This handler logs HTTP exceptions with context while maintaining
    the original response format for API consistency.

    Args:
        request: The FastAPI request object
        exc: The HTTP exception that was raised

    Returns:
        JSON response with error details
    """
    context = get_log_context()

    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR

    logger.log(
        log_level,
        "HTTP %d: %s",
        exc.status_code,
        exc.detail,
        extra={
            "event_type": "http_exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "headers": exc.headers,
            **context,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions with comprehensive logging.

    This handler catches all unhandled exceptions, logs them with full
    context and traceback information, and returns a generic error response
    to avoid leaking implementation details.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSON response with generic error message
    """
    context = get_log_context()

    request_info = {
        "path": request.url.path,
        "method": request.method,
        "query_params": str(request.query_params) if request.query_params else None,
        "client_ip": getattr(request.state, "client_ip", "unknown"),
        "user_agent": getattr(request.state, "user_agent", "unknown"),
    }

    logger.error(
        "Unhandled exception during request processing: %s",
        str(exc),
        exc_info=True,
        extra={
            "event_type": "unhandled_exception",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            **request_info,
            **context,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_id": context.get("request_id", "unknown"),
        },
    )


def setup_exception_logging() -> None:
    """
    Set up global exception logging for uncaught exceptions.

    This function installs a custom exception hook that logs uncaught exceptions
    before the application terminates, providing valuable debugging information.
    """
    original_excepthook = sys.excepthook

    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions by logging them with full context.

        Args:
            exc_type: The exception type
            exc_value: The exception instance
            exc_traceback: The traceback object
        """

        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            original_excepthook(exc_type, exc_value, exc_traceback)
            return

        try:
            context = get_log_context()
        except Exception:
            context = {}

        exception_info = {
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
            "traceback_lines": traceback.format_exception(exc_type, exc_value, exc_traceback),
        }

        logger.critical(
            "Uncaught exception: %s - %s",
            exc_type.__name__,
            str(exc_value),
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={
                "event_type": "uncaught_exception",
                **exception_info,
                **context,
            },
        )

        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_uncaught_exception


def log_exception_with_context(
    exc: Exception,
    message: str = "Exception occurred",
    level: int = logging.ERROR,
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exception with current context and additional information.

    This utility function provides a consistent way to log exceptions
    throughout the application with rich contextual information.

    Args:
        exc: The exception to log
        message: Custom message to include with the log
        level: Logging level to use
        extra_context: Additional context to include in the log
    """
    context = get_log_context()

    log_extra = {
        "event_type": "exception_logged",
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        **context,
    }

    if extra_context:
        log_extra.update(extra_context)

    logger.log(
        level,
        "%s: %s - %s",
        message,
        type(exc).__name__,
        str(exc),
        exc_info=True,
        extra=log_extra,
    )


class ContextualExceptionMixin:
    """
    Mixin class for adding contextual logging to custom exceptions.

    This mixin provides automatic logging capabilities to custom exception
    classes, ensuring that exceptions are logged with full context when raised.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._log_exception()

    def _log_exception(self):
        """Log this exception with context."""
        try:
            if isinstance(self, Exception):
                log_exception_with_context(
                    self,
                    message=f"{type(self).__name__} raised",
                    level=logging.ERROR,
                )
        except Exception:
            pass
