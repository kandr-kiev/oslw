"""Digest endpoints — newspaper digest generation.

Uses DigestService from Application Layer.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from oslw.api.v1.schemas import DigestResponse
from oslw.api.deps import get_settings, get_api_key
from oslw.config.settings import Settings
from oslw.application import DigestService
from oslw.config.logging import get_logger

router = APIRouter(tags=["digest"])
logger = get_logger("api.digest")


def get_digest_service(settings: Settings = Depends(get_settings)) -> DigestService:
    """Dependency injection for DigestService."""
    return DigestService(wiki_root=settings.wiki_root)


@router.get(
    "/today",
    response_model=DigestResponse,
    summary="Today's digest",
    description="Get today's newspaper digest",
)
def get_today_digest(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    digest_service: DigestService = Depends(get_digest_service),
) -> DigestResponse:
    """Get today's newspaper digest."""
    try:
        summary = digest_service.get_digest_summary(hours=hours)
        entries = digest_service.get_recent_entries(limit=100, hours=hours)

        return DigestResponse(
            date=summary.generated_at,
            total_articles=summary.total_entries,
            articles=[
                {
                    "title": e.page,
                    "slug": e.page.replace(" ", "-"),
                    "summary": e.description or "",
                    "created": e.timestamp,
                    "tags": [],
                }
                for e in entries
            ],
        )
    except Exception as e:
        logger.error("Error generating digest: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate",
    response_model=DigestResponse,
    summary="Generate digest",
    description="Generate a digest for specified period",
)
def generate_digest(
    hours: int = Query(24, ge=1, le=168),
    digest_service: DigestService = Depends(get_digest_service),
    api_key: str = Depends(get_api_key),
) -> DigestResponse:
    """Generate a digest."""
    try:
        summary = digest_service.get_digest_summary(hours=hours)
        entries = digest_service.get_recent_entries(limit=100, hours=hours)

        return DigestResponse(
            date=summary.generated_at,
            total_articles=summary.total_entries,
            articles=[
                {
                    "title": e.page,
                    "slug": e.page.replace(" ", "-"),
                    "summary": e.description or "",
                    "created": e.timestamp,
                    "tags": [],
                }
                for e in entries
            ],
        )
    except Exception as e:
        logger.error("Error generating digest: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
