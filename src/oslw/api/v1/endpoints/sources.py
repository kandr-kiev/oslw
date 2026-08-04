"""Source monitor endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from oslw.api.v1.schemas import (
    SourceListResponse,
    SourceCheckRequest,
)
from oslw.config.logging import get_logger

router = APIRouter(tags=["sources"])
logger = get_logger("api.sources")


@router.get(
    "/",
    response_model=SourceListResponse,
    summary="List monitored sources",
    description="Get all configured source monitors",
)
async def list_sources() -> SourceListResponse:
    """List all configured sources."""
    # TODO: Implement source listing
    return SourceListResponse(sources=[], total=0)


@router.post(
    "/check",
    summary="Check sources",
    description="Trigger a check of source monitors",
)
async def check_sources(request: SourceCheckRequest) -> dict:
    """Check sources for new content."""
    # TODO: Implement source checking
    logger.info("Checking sources: %s", request.source_name)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
