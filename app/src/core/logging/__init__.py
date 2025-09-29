"""
Structured logging module for the Bloom application.

This module provides a comprehensive logging system with:
- Structured JSON logging for production observability
- Contextual enrichment with request IDs, user info, etc.
- Environment-specific configurations
- Exception tracking and error handling
- Noise reduction and filtering capabilities

Usage:
    from src.core.logging import setup_logging, get_logger, add_to_log_context

    # Setup logging (usually done at application startup)
    setup_logging()

    # Get a logger
    logger = get_logger(__name__)

    # Use contextual logging
    with add_to_log_context(user_id="123", request_id="abc"):
        logger.info("Processing user request")
"""

from .config import get_logger, setup_exception_logging, setup_logging
from .exceptions import general_exception_handler, http_exception_handler, log_exception_with_context
from .filters import add_to_log_context, clear_log_context, get_log_context

__all__ = [
    "setup_logging",
    "setup_exception_logging",
    "get_logger",
    "add_to_log_context",
    "get_log_context",
    "clear_log_context",
    "http_exception_handler",
    "general_exception_handler",
    "log_exception_with_context",
]
