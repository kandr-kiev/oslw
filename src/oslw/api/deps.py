"""FastAPI dependency injection for OSLW.

Provides shared dependencies (settings, logger, database)
to API endpoints.
"""

from functools import lru_cache

from fastapi import Request

from oslw.config.settings import Settings, settings
from oslw.config.logging import get_logger


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached singleton)."""
    return settings


def get_logger_dep(request: Request) -> str:
    """Get logger name from request path."""
    path = request.url.path
    return f"oslw.api.{path.split('/')[3] if len(path.split('/')) > 3 else 'unknown'}"
