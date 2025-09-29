import contextvars
import logging
import os
import socket
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

_log_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("log_context", default={})


class BaseContextFilter(logging.Filter):
    """
    Base filter class that provides common context enrichment functionality.

    This filter serves as a foundation for other context filters and provides
    basic infrastructure for adding attributes to log records.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Process a log record and add context.

        Args:
            record: The LogRecord to process

        Returns:
            True to allow the record to be processed, False to drop it
        """
        self.add_context(record)
        return True

    def add_context(self, record: logging.LogRecord) -> None:
        """
        Add context to the log record. Override this method in subclasses.

        Args:
            record: The LogRecord to enrich with context
        """
        pass


class GlobalContextFilter(BaseContextFilter):
    """
    Filter that adds global application context to all log records.

    This filter enriches log records with static, application-wide information
    such as hostname, process ID, and other environment details that remain
    constant throughout the application's lifecycle.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)

        # Cache static values at initialization
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()

        # Get environment information
        self.environment = os.getenv("ENVIRONMENT", "unknown")
        self.app_name = os.getenv("APP_NAME", "bloom-api")
        self.app_version = os.getenv("APP_VERSION", "0.1.0")

    def add_context(self, record: logging.LogRecord) -> None:
        """
        Add global context attributes to the log record.

        Args:
            record: The LogRecord to enrich
        """
        record.hostname = self.hostname
        record.process_id = self.process_id
        record.environment = self.environment
        record.app_name = self.app_name
        record.app_version = self.app_version


class DynamicContextFilter(BaseContextFilter):
    """
    Filter that adds dynamic context from contextvars to log records.

    This filter retrieves context that changes during execution (like request IDs,
    user IDs, trace IDs) from contextvars and adds them to log records.
    """

    def add_context(self, record: logging.LogRecord) -> None:
        """
        Add dynamic context from contextvars to the log record.

        Args:
            record: The LogRecord to enrich
        """
        context = _log_context.get()
        for key, value in context.items():
            setattr(record, key, value)


class CombinedContextFilter(BaseContextFilter):
    """
    Filter that combines global and dynamic context filtering.

    This is a convenience filter that applies both global and dynamic context
    enrichment in a single filter to reduce configuration complexity.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)

        # Initialize the component filters
        self.global_filter = GlobalContextFilter(name)
        self.dynamic_filter = DynamicContextFilter(name)

    def add_context(self, record: logging.LogRecord) -> None:
        """
        Add both global and dynamic context to the log record.

        Args:
            record: The LogRecord to enrich
        """
        self.global_filter.add_context(record)
        self.dynamic_filter.add_context(record)


class NoiseReductionFilter(logging.Filter):
    """
    Filter for reducing log noise by suppressing known patterns.

    This filter helps reduce log volume and cost by dropping log records
    that match specific patterns, such as health checks or other high-volume,
    low-value log messages.
    """

    def __init__(
        self,
        name: str = "",
        suppress_patterns: Optional[list[str]] = None,
        suppress_loggers: Optional[list[str]] = None,
        min_level: Optional[int] = None,
    ) -> None:
        """
        Initialize the noise reduction filter.

        Args:
            name: Filter name
            suppress_patterns: List of substring patterns to suppress in log messages
            suppress_loggers: List of logger names to suppress
            min_level: Minimum log level to allow (drops everything below this level)
        """
        super().__init__(name)

        self.suppress_patterns = suppress_patterns or [
            "/health",
            "/metrics",
            "/ping",
            "heartbeat",
        ]
        self.suppress_loggers = suppress_loggers or []
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on configured patterns and rules.

        Args:
            record: The LogRecord to evaluate

        Returns:
            True to allow the record, False to suppress it
        """
        # Check minimum level
        if self.min_level and record.levelno < self.min_level:
            return False

        # Check logger suppression
        if record.name in self.suppress_loggers:
            return False

        # Check message pattern suppression
        message = record.getMessage()
        for pattern in self.suppress_patterns:
            if pattern in message:
                return False

        return True


class RequestIdFilter(BaseContextFilter):
    """
    Filter that ensures every log record has a request ID.

    This filter checks if a request ID is already present in the context,
    and if not, generates a new one. This ensures traceability across
    all log messages within a request.
    """

    def add_context(self, record: logging.LogRecord) -> None:
        """
        Ensure the log record has a request ID.

        Args:
            record: The LogRecord to process
        """
        context = _log_context.get()

        # Only add request_id if it's not already present
        if "request_id" not in context:
            request_id = str(uuid.uuid4())
            # Update the context for this request
            new_context = {**context, "request_id": request_id}
            _log_context.set(new_context)
            record.request_id = request_id
        else:
            record.request_id = context["request_id"]


# Context management utilities


@contextmanager
def add_to_log_context(**kwargs: Any):
    """
    Context manager for temporarily adding context to logs.

    This context manager allows you to add context that will be automatically
    included in all log messages within the context block. The context is
    properly cleaned up when exiting the block.

    Args:
        **kwargs: Key-value pairs to add to the logging context

    Example:
        with add_to_log_context(user_id="123", request_id="abc"):
            logger.info("Processing request")  # Will include user_id and request_id
    """
    current_context = _log_context.get()
    new_context = {**current_context, **kwargs}

    # Set the new context and get the token for restoration
    token = _log_context.set(new_context)

    try:
        yield
    finally:
        _log_context.reset(token)


def get_log_context() -> Dict[str, Any]:
    """
    Get the current logging context.

    Returns:
        Dictionary containing the current logging context
    """
    return _log_context.get()


def clear_log_context() -> None:
    """
    Clear the current logging context.

    This function resets the logging context to an empty state.
    """
    _log_context.set({})
