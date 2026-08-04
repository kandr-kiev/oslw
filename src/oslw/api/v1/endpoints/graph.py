"""Graph endpoints — knowledge graph operations.

Uses GraphService from Application Layer.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from oslw.api.v1.schemas import GraphResponse, GraphNode, GraphEdge
from oslw.api.deps import get_settings
from oslw.config.settings import Settings
from oslw.application import GraphService
from oslw.config.logging import get_logger

router = APIRouter(tags=["graph"])
logger = get_logger("api.graph")


def get_graph_service(settings: Settings = Depends(get_settings)) -> GraphService:
    """Dependency injection for GraphService."""
    return GraphService(wiki_root=settings.wiki_root)


@router.get(
    "/",
    response_model=GraphResponse,
    summary="Get knowledge graph",
    description="Get the wiki knowledge graph as nodes and edges",
)
async def get_graph(
    graph_service: GraphService = Depends(get_graph_service),
) -> GraphResponse:
    """Get the wiki knowledge graph."""
    try:
        graph_dict = await graph_service.generate_graph()

        nodes = [
            GraphNode(
                id=node.get("slug", ""),
                label=node.get("title", ""),
                type=node.get("category", "wiki"),
            )
            for node in graph_dict.get("nodes", {}).values()
        ]

        edges = [
            GraphEdge(
                source=edge.get("source", ""),
                target=edge.get("target", ""),
                label=edge.get("label", ""),
            )
            for edge in graph_dict.get("edges", [])
        ]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            total=len(nodes),
        )
    except Exception as e:
        logger.error("Error getting graph: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate",
    response_model=GraphResponse,
    summary="Generate graph",
    description="Regenerate the knowledge graph from wiki pages",
)
async def generate_graph(
    graph_service: GraphService = Depends(get_graph_service),
) -> GraphResponse:
    """Generate the knowledge graph from wiki wikilinks."""
    try:
        graph_dict = await graph_service.generate_graph()

        nodes = [
            GraphNode(
                id=node.get("slug", ""),
                label=node.get("title", ""),
                type=node.get("category", "wiki"),
            )
            for node in graph_dict.get("nodes", {}).values()
        ]

        edges = [
            GraphEdge(
                source=edge.get("source", ""),
                target=edge.get("target", ""),
                label=edge.get("label", ""),
            )
            for edge in graph_dict.get("edges", [])
        ]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            total=len(nodes),
        )
    except Exception as e:
        logger.error("Error generating graph: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
