"""Logging configuration for OSLW.

Configures structured logging with file and console handlers.
Uses Python's logging module with formatting.
"""

import logging
import sys
from pathlib import Path

from oslw.config.settings import Settings

# ============================================================================
# Log format
# ============================================================================
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M"


def setup_logging(settings: Settings) -> None:
    """Configure root logger based on settings.

    Sets up:
    - Console handler (stderr) with log level
    - File handler (if log_dir exists)
    - Formatter with timestamp and level
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(
        DEFAULT_FORMAT,
        datefmt=DATE_FORMAT,
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handlers (one per workflow)
    log_dir = settings.log_dir
    if log_dir and log_dir.exists():
        file_handler = logging.FileHandler(
            log_dir / "oslw.log",
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt=DATE_FORMAT,
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure sub-loggers
    for name in [
        "oslw.api",
        "oslw.domain",
        "oslw.infrastructure",
        "oslw.application",
        "oslw.cli",
    ]:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a named logger.

    Usage:
        logger = get_logger("oslw.domain.wiki")
        logger.info("Сторінку створено: %s", slug)
    """
    return logging.getLogger(f"oslw.{name}")
