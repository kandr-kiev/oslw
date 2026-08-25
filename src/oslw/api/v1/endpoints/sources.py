"""Source monitor endpoints — content source management.

Uses SourceService from Application Layer.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from oslw.api.v1.schemas import (
    SourceListResponse,
    SourceCheckRequest,
    SourceInfo,
)
from oslw.api.deps import get_settings, get_api_key
from oslw.config.settings import Settings
from oslw.application import SourceService
from oslw.config.logging import get_logger

router = APIRouter(tags=["sources"])
logger = get_logger("api.sources")


def get_source_service(settings: Settings = Depends(get_settings)) -> SourceService:
    """Dependency injection for SourceService."""
    return SourceService(wiki_root=settings.wiki_root)


@router.get(
    "/",
    response_model=SourceListResponse,
    summary="List monitored sources",
    description="Get all configured source monitors",
)
def list_sources(
    source_service: SourceService = Depends(get_source_service),
) -> SourceListResponse:
    """List all configured sources."""
    try:
        stats = source_service.list_sources()

        sources = [
            SourceInfo(
                name=s.name,
                type=s.type,
                url="",  # Don't expose URLs
                last_checked=s.last_checked,
                status="ok" if not s.last_error else "error",
                articles_count=s.articles_count,
            )
            for s in stats
        ]

        return SourceListResponse(
            sources=sources,
            total=len(sources),
        )
    except Exception as e:
        logger.error("Помилка списку джерел: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/check",
    summary="Check sources",
    description="Trigger a check of source monitors",
)
def check_sources(
    request: SourceCheckRequest,
    source_service: SourceService = Depends(get_source_service),
    api_key: str = Depends(get_api_key),
) -> dict:
    """Check sources for new content."""
    try:
        results = source_service.monitor_sources()

        return {
            "success": True,
            "results": results,
            "source_filter": request.source_name,
        }
    except Exception as e:
        logger.error("Помилка перевірки джерел: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
