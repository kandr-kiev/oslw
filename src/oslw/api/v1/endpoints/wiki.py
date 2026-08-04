"""Wiki page endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from oslw.api.v1.schemas import (
    WikiPageCreate,
    WikiPageUpdate,
    WikiPageResponse,
)
from oslw.config.logging import get_logger

router = APIRouter(tags=["wiki"])
logger = get_logger("api.wiki")


@router.get(
    "/",
    response_model=list[WikiPageResponse],
    summary="List wiki pages",
    description="Get all wiki pages with optional filters",
)
async def list_pages(
    type: Optional[str] = Query(None, description="Filter by page type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List wiki pages with pagination and filters."""
    # TODO: Implement actual page listing from wiki root
    return []


@router.get(
    "/{slug}",
    response_model=WikiPageResponse,
    summary="Get wiki page",
    description="Get a single wiki page by slug",
)
async def get_page(slug: str) -> WikiPageResponse:
    """Get a wiki page by its slug."""
    # TODO: Implement actual page retrieval
    raise HTTPException(
        status_code=404,
        detail=f"Wiki page not found: {slug}",
    )


@router.post(
    "/",
    response_model=WikiPageResponse,
    status_code=201,
    summary="Create wiki page",
    description="Create a new wiki page",
)
async def create_page(page: WikiPageCreate) -> WikiPageResponse:
    """Create a new wiki page."""
    # TODO: Implement actual page creation
    logger.info("Creating page: %s - %s", page.slug, page.title)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )


@router.put(
    "/{slug}",
    response_model=WikiPageResponse,
    summary="Update wiki page",
    description="Update an existing wiki page",
)
async def update_page(slug: str, page: WikiPageUpdate) -> WikiPageResponse:
    """Update an existing wiki page."""
    # TODO: Implement actual page update
    logger.info("Updating page: %s", slug)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )


@router.delete(
    "/{slug}",
    status_code=204,
    summary="Delete wiki page",
    description="Delete a wiki page by slug",
)
async def delete_page(slug: str) -> None:
    """Delete a wiki page."""
    # TODO: Implement actual page deletion
    logger.info("Deleting page: %s", slug)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
