"""Configuration package."""

from oslw.config.settings import Settings, settings
from oslw.config.logging import setup_logging, get_logger

__all__ = ["Settings", "settings", "setup_logging", "get_logger"]
