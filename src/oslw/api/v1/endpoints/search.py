"""Search endpoints."""

from fastapi import APIRouter, HTTPException, Query

from oslw.api.v1.schemas import SearchRequest, SearchResponse
from oslw.config.logging import get_logger

router = APIRouter(tags=["search"])
logger = get_logger("api.search")


@router.post(
    "/",
    response_model=SearchResponse,
    summary="Search wiki",
    description="Search wiki pages by query",
)
async def search_wiki(request: SearchRequest) -> SearchResponse:
    """Search wiki pages."""
    # TODO: Implement actual search
    logger.info("Searching wiki: %s (limit=%d, type=%s)", request.query, request.limit, request.type)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
