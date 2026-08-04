"""GraphService — business logic for knowledge graph operations.

Orchestrates GraphGenerator, GraphQuery and FileManager to provide
complete knowledge graph management.

Usage:
    from oslw.config import settings
    from oslw.application import GraphService

    service = GraphService(wiki_root=settings.wiki_root)
    graph = await service.generate_graph()
    results = await service.search("RAG", depth=2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.graph.generator import GraphGenerator
from oslw.domain.graph.query import GraphQuery
from oslw.infrastructure.database import FileManager

logger = get_logger("application.graph_service")


@dataclass
class GraphStats:
    """Statistics about the knowledge graph.

    Attributes:
        nodes: Total number of nodes
        edges: Total number of edges
        categories: Number of node categories
        density: Graph density (edges / possible_edges)
    """

    nodes: int = 0
    edges: int = 0
    categories: int = 0
    density: float = 0.0


@dataclass
class SearchResults:
    """Results from graph search.

    Attributes:
        query: Original search query
        results: List of matching pages with relevance scores
        total: Total number of results
    """

    query: str
    results: list[dict] = field(default_factory=list)
    total: int = 0


class GraphService:
    """Knowledge graph management service.

    Provides:
    - Generate graph from wiki pages
    - Search graph with BFS traversal
    - Get graph statistics
    - Export graph to JSON

    Usage:
        service = GraphService(wiki_root=Path("./wiki"))
        graph = await service.generate_graph()
        results = await service.search("transformers", depth=2)
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize GraphService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.generator = GraphGenerator(wiki_root=Path(wiki_root))
        self.query = GraphQuery(wiki_root=Path(wiki_root))

    async def generate_graph(self) -> dict:
        """Generate knowledge graph from wiki pages.

        Scans all wiki pages, extracts wikilinks,
        and builds a directed graph.

        Returns:
            Graph dictionary with nodes and edges
        """
        graph = self.generator.generate()
        logger.info("Generated graph: %d nodes, %d edges",
                   len(graph.nodes), len(graph.edges))
        return graph.to_dict()

    async def search(self, query: str, depth: int = 2,
                    limit: int = 10) -> SearchResults:
        """Search knowledge graph for relevant pages.

        Performs fuzzy matching and BFS traversal
        to find pages related to the query.

        Args:
            query: Search query string
            depth: BFS traversal depth
            limit: Maximum results

        Returns:
            SearchResults with matching pages
        """
        results = self.query.search(query, depth=depth, limit=limit)
        logger.info("Search '%s' returned %d results",
                   query, len(results))
        return SearchResults(
            query=query,
            results=results,
            total=len(results),
        )

    async def get_stats(self) -> GraphStats:
        """Get graph statistics.

        Returns:
            GraphStats with current statistics
        """
        graph = self.generator.generate()

        # Count categories
        categories = set(node.get("category", "unknown")
                        for node in graph.nodes.values())

        # Calculate density
        n = len(graph.nodes)
        max_edges = n * (n - 1) if n > 1 else 1
        density = len(graph.edges) / max_edges if max_edges > 0 else 0.0

        return GraphStats(
            nodes=len(graph.nodes),
            edges=len(graph.edges),
            categories=len(categories),
            density=density,
        )

    async def export_graph(self, output_path: Optional[str | Path] = None) -> Path:
        """Export graph to JSON file.

        Args:
            output_path: Optional output path (defaults to graph-from-wiki.json)

        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = self.file_manager.wiki_root / "graph-from-wiki.json"

        graph = self.generator.generate()
        graph.to_json(output_path)

        logger.info("Exported graph to %s", output_path)
        return Path(output_path)

    async def get_node(self, slug: str) -> Optional[dict]:
        """Get a single graph node by slug.

        Args:
            slug: Node slug

        Returns:
            Node dictionary if found, None otherwise
        """
        graph = self.generator.generate()
        return graph.nodes.get(slug)

    async def get_connections(self, slug: str) -> list[dict]:
        """Get all connections for a node.

        Args:
            slug: Node slug

        Returns:
            List of connection dictionaries
        """
        graph = self.generator.generate()

        connections = []
        for edge in graph.edges:
            if edge["source"] == slug:
                connections.append({
                    "target": edge["target"],
                    "label": edge.get("label", ""),
                })
            elif edge["target"] == slug:
                connections.append({
                    "source": edge["source"],
                    "label": edge.get("label", ""),
                    "direction": "incoming",
                })

        return connections
