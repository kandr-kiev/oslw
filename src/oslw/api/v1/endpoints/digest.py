"""Digest endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from oslw.api.v1.schemas import DigestResponse
from oslw.config.logging import get_logger

router = APIRouter(tags=["digest"])
logger = get_logger("api.digest")


@router.get(
    "/today",
    response_model=DigestResponse,
    summary="Today's digest",
    description="Get today's newspaper digest",
)
async def get_today_digest(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
) -> DigestResponse:
    """Get today's newspaper digest."""
    # TODO: Implement digest generation
    logger.info("Generating digest for last %d hours", hours)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )


@router.post(
    "/generate",
    response_model=DigestResponse,
    summary="Generate digest",
    description="Generate a digest for specified period",
)
async def generate_digest(hours: int = Query(24, ge=1, le=168)) -> DigestResponse:
    """Generate a digest."""
    # TODO: Implement digest generation
    logger.info("Generating digest for last %d hours", hours)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
