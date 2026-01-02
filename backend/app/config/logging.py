"""Structured logging configuration using structlog."""

import logging
import sys
from pathlib import Path

import structlog

from app.config.settings import settings


def configure_logging() -> None:
    """
    Configure structlog for the application.

    - JSON logging for production
    - Pretty console logging for development
    - Request ID tracking
    - Exception formatting
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Choose processors based on environment
    if settings.environment == "production":
        # JSON logging for production (machine-readable)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Pretty console logging for development (human-readable)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add caller info (filename, function name, line number)
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # Format exception tracebacks
            structlog.processors.ExceptionRenderer(),
            # Stack info for debugging
            structlog.processors.StackInfoRenderer(),
            # Format for output
            renderer,
        ],
        # Wrapper class for logger
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        # Context class for storing request-specific data
        context_class=dict,
        # Logger factory
        logger_factory=structlog.PrintLoggerFactory(),
        # Cache logger instances
        cache_logger_on_first_use=True,
    )

    # Create logs directory if logging to file
    if settings.log_to_file:
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add file handler
        file_handler = logging.FileHandler(settings.log_file_path)
        file_handler.setLevel(getattr(logging, settings.log_level.upper()))
        logging.root.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger

    Usage:
        logger = get_logger(__name__)
        logger.info("user_authenticated", user_id="admin", ip_address="127.0.0.1")
    """
    return structlog.get_logger(name)
