import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from src.core.config import settings


def get_logging_config() -> Dict[str, Any]:
    """
    Get the logging configuration dictionary based on the current environment.

    Returns:
        Dictionary containing the complete logging configuration
    """
    # Base configuration structure
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {},
        "filters": {},
        "handlers": {},
        "loggers": {},
        "root": {
            "level": "WARNING",
            "handlers": [],
        },
    }

    if settings.ENVIRONMENT == "local":
        config["formatters"] = {
            "console": {
                "()": "src.core.logging.formatters.ConsoleFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "rename_fields": {
                    "levelname": "level",
                    "asctime": "timestamp",
                    "name": "logger",
                },
            },
            "detailed": {
                "()": "src.core.logging.formatters.StructuredExceptionJsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "rename_fields": {
                    "levelname": "level",
                    "asctime": "timestamp",
                    "name": "logger",
                    "pathname": "file_path",
                    "lineno": "line_number",
                },
            },
        }
    else:
        config["formatters"] = {
            "production": {
                "()": "src.core.logging.formatters.ProductionFormatter",
                "format": (
                    "%(asctime)s %(name)s %(levelname)s %(message)s "
                    "%(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d"
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "rename_fields": {
                    "levelname": "level",
                    "asctime": "timestamp",
                    "name": "logger",
                    "pathname": "file_path",
                    "lineno": "line_number",
                    "funcName": "function_name",
                    "process": "process_id",
                    "thread": "thread_id",
                },
            }
        }

    config["filters"] = {
        "context_filter": {
            "()": "src.core.logging.filters.CombinedContextFilter",
        },
        "noise_reduction": {
            "()": "src.core.logging.filters.NoiseReductionFilter",
            "suppress_patterns": ["/health", "/metrics", "/ping", "heartbeat"],
        },
        "request_id": {
            "()": "src.core.logging.filters.RequestIdFilter",
        },
    }

    if settings.ENVIRONMENT == "local":
        config["handlers"] = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "console",
                "filters": ["context_filter", "request_id"],
                "stream": "ext://sys.stdout",
            },
            "error_file": {
                "class": "logging.FileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filters": ["context_filter"],
                "filename": "logs/errors.log",
                "mode": "a",
            },
        }
        config["root"]["handlers"] = ["console"]
    else:
        config["handlers"] = {
            "json_stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "production",
                "filters": ["context_filter", "noise_reduction"],
                "stream": "ext://sys.stdout",
            },
            "error_stderr": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "production",
                "filters": ["context_filter"],
                "stream": "ext://sys.stderr",
            },
        }
        config["root"]["handlers"] = ["json_stdout", "error_stderr"]

    # Configure application loggers
    app_level = "DEBUG" if settings.ENVIRONMENT == "local" else "INFO"

    config["loggers"] = {
        # Main application logger
        "src": {
            "level": app_level,
            "handlers": config["root"]["handlers"],
            "propagate": False,
        },
        # FastAPI and related loggers
        "fastapi": {
            "level": "INFO",
            "propagate": True,
        },
        "uvicorn": {
            "level": "INFO",
            "propagate": True,
        },
        "uvicorn.access": {
            "level": "WARNING",  # Disable access logs - we handle this in middleware
            "propagate": False,
        },
        # Database loggers
        "sqlalchemy": {
            "level": "WARNING",
            "propagate": True,
        },
        "sqlalchemy.engine": {
            "level": "INFO" if settings.ENVIRONMENT == "local" else "WARNING",
            "propagate": True,
        },
        # Third-party loggers
        "boto3": {
            "level": "WARNING",
            "propagate": True,
        },
        "botocore": {
            "level": "WARNING",
            "propagate": True,
        },
        "celery": {
            "level": "INFO",
            "propagate": True,
        },
    }

    return config


def load_config_from_yaml(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load logging configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing the logging configuration, or None if file doesn't exist
    """
    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load logging config from {config_path}: {e}", file=sys.stderr)
        return None


def setup_logging(config_override: Optional[Dict[str, Any]] = None) -> None:
    """
    Set up logging configuration for the application.

    This function configures logging using either:
    1. A provided configuration override
    2. A YAML configuration file (if present)
    3. The default programmatic configuration

    Args:
        config_override: Optional dictionary to override the default configuration
    """
    config = None

    # 1. Try to use provided override
    if config_override:
        config = config_override
    else:
        # 2. Try to load from YAML file
        config_path = Path(settings.BASE_DIR) / "config" / f"logging.{settings.ENVIRONMENT}.yaml"
        config = load_config_from_yaml(config_path)

        # Fallback to general logging.yaml
        if config is None:
            config_path = Path(settings.BASE_DIR) / "config" / "logging.yaml"
            config = load_config_from_yaml(config_path)

    # 3. Use default programmatic configuration
    if config is None:
        config = get_logging_config()

    # Ensure log directory exists for file handlers
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)

    # Apply the configuration
    try:
        logging.config.dictConfig(config)
    except Exception as e:
        print(f"Failed to configure logging: {e}", file=sys.stderr)
        # Fallback to basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
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
        Handle uncaught exceptions by logging them.

        Args:
            exc_type: The exception type
            exc_value: The exception instance
            exc_traceback: The traceback object
        """
        # Don't log KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            original_excepthook(exc_type, exc_value, exc_traceback)
            return

        # Log the uncaught exception
        logger = logging.getLogger(__name__)
        logger.critical(
            "Uncaught exception, application will terminate",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

        # Call the original exception hook
        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_uncaught_exception


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    This is a convenience function that follows the recommended pattern
    of using __name__ for logger names while ensuring consistent configuration.

    Args:
        name: The logger name (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
