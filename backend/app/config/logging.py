"""Structured logging configuration using structlog."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import structlog

from app.config.settings import settings

# Generate timestamp for log filename at module load time (server start)
_server_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")


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
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log filename (e.g., acodeaday_20260110_080612.log)
        log_stem = log_path.stem  # e.g., "acodeaday"
        log_suffix = log_path.suffix or ".log"  # e.g., ".log"
        timestamped_log_file = log_dir / f"{log_stem}_{_server_start_time}{log_suffix}"

        # Add file handler with timestamped filename
        file_handler = logging.FileHandler(timestamped_log_file)
        file_handler.setLevel(getattr(logging, settings.log_level.upper()))
        # Add timestamp formatter for file logs
        file_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
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
