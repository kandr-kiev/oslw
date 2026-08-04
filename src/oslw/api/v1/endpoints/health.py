"""Health check endpoints."""

from fastapi import APIRouter

from oslw.api.v1.schemas import HealthResponse
from oslw.config.settings import settings
from pathlib import Path

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the OSLW service is running",
)
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        wiki_root=str(settings.wiki_root),
        wiki_exists=settings.wiki_root.exists(),
    )
