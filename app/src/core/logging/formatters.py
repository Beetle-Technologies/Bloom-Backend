import traceback
from typing import Any, Dict, Optional

from pythonjsonlogger.json import JsonFormatter


class StructuredExceptionJsonFormatter(JsonFormatter):
    """
    A JSON formatter that provides structured exception handling.

    This formatter enhances the standard JSON logging by:
    - Converting Python tracebacks into structured data
    - Supporting field renaming for consistency
    - Preserving all LogRecord attributes while customizing output format
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        json_default: Any = None,
        json_encoder: Any = None,
        json_serializer: Any = None,
        json_decoder: Any = None,
        json_indent: Optional[int] = None,
        json_ensure_ascii: bool = True,
        prefix: str = "",
        rename_fields: Optional[Dict[str, str]] = None,
        static_fields: Optional[Dict[str, Any]] = None,
        reserved_attrs: Optional[list] = None,
        **kwargs,  # Add this to catch any extra arguments
    ):
        """
        Initialize the structured JSON formatter.

        Args:
            fmt: Format string for included fields
            datefmt: Date format string
            json_default: Default function for JSON serialization
            json_encoder: Custom JSON encoder class
            json_serializer: Custom JSON serializer function
            json_decoder: Custom JSON decoder
            json_indent: JSON indentation level
            json_ensure_ascii: Whether to escape non-ASCII characters
            prefix: Prefix for log messages
            rename_fields: Dictionary mapping original field names to new names
            static_fields: Static fields to include in every log record
            reserved_attrs: List of reserved attributes to exclude from output
        """
        # Filter out any unknown kwargs that might come from YAML config
        valid_kwargs = {
            "fmt": fmt,
            "datefmt": datefmt,
            "json_default": json_default,
            "json_encoder": json_encoder,
            "json_serializer": json_serializer,
            "json_decoder": json_decoder,
            "json_indent": json_indent,
            "json_ensure_ascii": json_ensure_ascii,
            "prefix": prefix,
            "rename_fields": rename_fields,
            "static_fields": static_fields,
            "reserved_attrs": reserved_attrs,
        }

        # Remove None values
        valid_kwargs = {k: v for k, v in valid_kwargs.items() if v is not None}

        super().__init__(**valid_kwargs)

    def add_fields(self, log_record: Dict[str, Any], record: Any, message_dict: Dict[str, Any]) -> None:
        """
        Add fields to the log record, including structured exception data.

        This method processes the LogRecord and adds structured exception information
        if an exception is present, while preserving all other fields.

        Args:
            log_record: The dictionary that will become the JSON log output
            record: The original LogRecord object
            message_dict: The message dictionary from the formatter
        """
        super().add_fields(log_record, record, message_dict)

        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info

            exception_data = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "traceback": None,
            }

            if exc_traceback:
                exception_data["traceback"] = traceback.format_exception(exc_type, exc_value, exc_traceback)

            log_record["exception"] = exception_data

            log_record.pop("exc_info", None)
            log_record.pop("exc_text", None)


class ConsoleFormatter(JsonFormatter):
    """
    A simplified JSON formatter optimized for console/development output.

    This formatter provides a cleaner output for development environments
    while maintaining structured logging capabilities.
    """

    def __init__(self, **kwargs):
        fmt = kwargs.pop("format", "%(asctime)s %(name)s %(levelname)s %(message)s")
        datefmt = kwargs.pop("datefmt", "%Y-%m-%d %H:%M:%S")
        rename_fields = kwargs.pop("rename_fields", {})

        default_rename_fields = {
            "levelname": "level",
            "asctime": "timestamp",
            "name": "logger",
        }

        rename_fields = {**default_rename_fields, **rename_fields}

        super().__init__(fmt=fmt, datefmt=datefmt, rename_fields=rename_fields, **kwargs)


class ProductionFormatter(StructuredExceptionJsonFormatter):
    """
    A comprehensive formatter optimized for production environments.

    This formatter includes all available fields and comprehensive error tracking
    for production observability requirements.
    """

    def __init__(self, **kwargs):
        fmt = kwargs.pop("format", None)
        if fmt is None:
            fmt = (
                "%(asctime)s %(name)s %(levelname)s %(message)s "
                "%(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d"
            )

        datefmt = kwargs.pop("datefmt", "%Y-%m-%dT%H:%M:%S")
        rename_fields = kwargs.pop("rename_fields", {})

        default_rename_fields = {
            "levelname": "level",
            "asctime": "timestamp",
            "name": "logger",
            "pathname": "file_path",
            "lineno": "line_number",
            "funcName": "function_name",
            "process": "process_id",
            "thread": "thread_id",
        }

        rename_fields = {**default_rename_fields, **rename_fields}

        super().__init__(fmt=fmt, datefmt=datefmt, rename_fields=rename_fields, **kwargs)
