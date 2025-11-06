"""
Logging configuration for Anita Backend
"""
import logging
import sys
import os
from typing import Optional


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure logging for the application

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, reads from LOG_LEVEL environment variable (default: INFO)
    """
    # Get log level from parameter or environment variable
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Validate log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override any existing configuration
    )

    # Set specific log levels for third-party libraries
    # (to reduce noise from verbose libraries)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Set our application modules to use the configured level
    logging.getLogger("services").setLevel(numeric_level)
    logging.getLogger("routers").setLevel(numeric_level)

    # Log that logging has been configured
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    logger.debug("Debug logging is enabled")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module

    Args:
        name: Name of the module (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
