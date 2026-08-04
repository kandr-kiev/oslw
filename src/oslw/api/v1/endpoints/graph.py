"""Graph endpoints."""

from fastapi import APIRouter, HTTPException

from oslw.api.v1.schemas import GraphResponse
from oslw.config.logging import get_logger

router = APIRouter(tags=["graph"])
logger = get_logger("api.graph")


@router.get(
    "/",
    response_model=GraphResponse,
    summary="Get knowledge graph",
    description="Get the wiki knowledge graph as nodes and edges",
)
async def get_graph() -> GraphResponse:
    """Get the wiki knowledge graph."""
    # TODO: Implement graph loading from graph-from-wiki.json
    return GraphResponse(nodes=[], edges=[], total=0)


@router.post(
    "/generate",
    response_model=GraphResponse,
    summary="Generate graph",
    description="Regenerate the knowledge graph from wiki pages",
)
async def generate_graph() -> GraphResponse:
    """Generate the knowledge graph from wiki wikilinks."""
    # TODO: Implement graph generation
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
