"""FastAPI routes for knowledge graph operations.

Provides REST API endpoints for the knowledge graph:
- GET /api/graph/stats - graph statistics
- GET /api/graph/export - export graph to JSON
- GET /api/graph/node/{slug} - get single node
- GET /api/graph/connections/{slug} - get node connections
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Optional

from oslw.application import GraphService
from oslw.config.settings import settings
from oslw.config.logging import get_logger

logger = get_logger("oslw.api.graph")

router = APIRouter(prefix="/graph", tags=["graph"])


def get_graph_service() -> GraphService:
    """Create GraphService instance from settings."""
    return GraphService(wiki_root=settings.wiki_root)


@router.get("/stats", summary="Graph statistics")
async def graph_stats():
    """Get knowledge graph statistics."""
    try:
        svc = get_graph_service()
        stats = svc.get_stats()
        return {
            "nodes": stats.nodes,
            "edges": stats.edges,
            "categories": stats.categories,
            "density": round(stats.density, 6),
        }
    except Exception as e:
        logger.error("Помилка отримання статистики графа: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export graph to JSON")
async def export_graph(output_dir: Optional[str] = None):
    """Export knowledge graph to JSON file.

    Args:
        output_dir: Custom output directory (default: wiki_root/)
    """
    try:
        svc = get_graph_service()
        if output_dir:
            path = svc.export_graph(output_dir=output_dir)
        else:
            path = svc.export_graph()

        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "path": str(path),
            "nodes": len(data.get("nodes", [])),
            "edges": len(data.get("edges", [])),
            "content": data,
        }
    except Exception as e:
        logger.error("Помилка експорту графа: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{slug}", summary="Get graph node by slug")
async def get_node(slug: str):
    """Get a single graph node by slug."""
    try:
        svc = get_graph_service()
        node = svc.get_node(slug)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {slug}")
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Помилка отримання вузла %s: %s", slug, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{slug}", summary="Get node connections")
async def get_node_connections(slug: str):
    """Get all connections (edges) for a graph node."""
    try:
        svc = get_graph_service()
        connections = svc.get_connections(slug)
        return {
            "slug": slug,
            "connections": connections,
            "total": len(connections),
        }
    except Exception as e:
        logger.error("Помилка отримання зв'язків для %s: %s", slug, e)
        raise HTTPException(status_code=500, detail=str(e))
