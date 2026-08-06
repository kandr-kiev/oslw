"""FastAPI dependency injection for OSLW.

Provides shared dependencies (settings, logger, database)
to API endpoints.
"""

from functools import lru_cache

from fastapi import HTTPException, Query, Request
from starlette.status import HTTP_403_FORBIDDEN

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


def get_api_key(
    api_key: str = Header(None, description="API key for authentication"),
    settings: Settings = get_settings(),
) -> str:
    """Validate API key from header."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key
