"""Search endpoints — wiki search functionality.

Uses IndexService and GraphService from Application Layer.
"""

from fastapi import APIRouter, HTTPException, Depends

from oslw.api.v1.schemas import SearchRequest, SearchResponse, SearchHit
from oslw.api.deps import get_settings
from oslw.config.settings import Settings
from oslw.application import IndexService, GraphService
from oslw.config.logging import get_logger

router = APIRouter(tags=["search"])
logger = get_logger("api.search")


def get_services(settings: Settings = Depends(get_settings)):
    """Dependency injection for services."""
    return IndexService(wiki_root=settings.wiki_root), GraphService(wiki_root=settings.wiki_root)


@router.post(
    "/",
    response_model=SearchResponse,
    summary="Search wiki",
    description="Search wiki pages by query",
)
async def search_wiki(
    request: SearchRequest,
    services: tuple = Depends(get_services),
) -> SearchResponse:
    """Search wiki pages."""
    try:
        index_service, graph_service = services
        query = request.query

        # Search in index
        index_hits = await index_service.search_index(query)

        # Search in graph
        graph_results = await graph_service.search(query, depth=1, limit=request.limit)

        # Combine results (deduplicate by slug)
        seen_slugs = set()
        hits = []

        for entry in index_hits[:request.limit]:
            hits.append(SearchHit(
                slug=entry.slug,
                title=entry.title,
                description=entry.description,
                score=0.8,
                type=entry.type,
                tags=entry.tags,
            ))
            seen_slugs.add(entry.slug)

        for result in graph_results.results[:request.limit]:
            slug = result.get("slug", "")
            if slug not in seen_slugs:
                hits.append(SearchHit(
                    slug=slug,
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    score=result.get("score", 0.5),
                    type=result.get("category", ""),
                    tags=[],
                ))
                seen_slugs.add(slug)

        # Apply type filter if specified
        if request.type:
            hits = [h for h in hits if h.type == request.type]

        return SearchResponse(
            query=query,
            total=len(hits),
            hits=hits[:request.limit],
        )
    except Exception as e:
        logger.error("Error searching wiki: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
