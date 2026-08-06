"""GraphService — business logic for knowledge graph operations.

Orchestrates GraphGenerator, GraphQuery and FileManager to provide
complete knowledge graph management.

Usage:
    from oslw.config import settings
    from oslw.application import GraphService

    service = GraphService(wiki_root=settings.wiki_root)
    graph = service.generate_graph()
    results = service.search("RAG", depth=2)
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
        graph = service.generate_graph()
        results = service.search("transformers", depth=2)
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize GraphService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.generator = GraphGenerator(wiki_root=Path(wiki_root))
        self.query = GraphQuery(wiki_root=Path(wiki_root))

    def generate_graph(self, force: bool = False) -> dict:
        """Generate knowledge graph from wiki pages.

        Scans all wiki pages, extracts wikilinks,
        and builds a directed graph. Uses cached graph if available.
        Automatically exports to disk after generation.

        Args:
            force: If True, regenerate from scratch.

        Returns:
            Graph dictionary with nodes and edges
        """
        graph = self.generator.generate(force=force)
        # Handle both dict (cached) and object (generated) return types
        if isinstance(graph, dict):
            logger.info("Loaded cached graph: %d nodes, %d edges",
                       len(graph.get("nodes", {})), len(graph.get("edges", [])))
        else:
            logger.info("Generated graph: %d nodes, %d edges",
                       len(graph.nodes), len(graph.edges))
            graph = graph.to_dict()

        # Persist graph to disk
        self.export_graph()

        return graph

    def search(self, query: str, depth: int = 2,
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

    def _get_graph_dict(self, force: bool = False) -> dict:
        """Get graph as a normalized dict (cached or regenerated)."""
        result = self.generator.generate(force=force)
        if isinstance(result, dict):
            return result
        return result.to_dict()

    def get_stats(self) -> GraphStats:
        """Get graph statistics."""
        graph = self._get_graph_dict()

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Count categories (nodes is a list of dicts with 'type' or 'file_type')
        categories = set()
        for node in nodes:
            cat = node.get("type", node.get("file_type", "unknown"))
            categories.add(cat)

        # Calculate density
        n = len(nodes)
        max_edges = n * (n - 1) if n > 1 else 1
        density = len(edges) / max_edges if max_edges > 0 else 0.0

        return GraphStats(
            nodes=n,
            edges=len(edges),
            categories=len(categories),
            density=density,
        )

    def export_graph(self, output_path: Optional[str | Path] = None) -> Path:
        """Export graph to JSON file."""
        if output_path is None:
            output_path = self.file_manager.wiki_root / "graph-from-wiki.json"

        graph = self._get_graph_dict()
        import json
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("Exported graph to %s", output_path)
        return Path(output_path)

    def get_node(self, slug: str) -> Optional[dict]:
        """Get a single graph node by slug."""
        graph = self._get_graph_dict()
        nodes = graph.get("nodes", [])
        for node in nodes:
            if node.get("id") == slug:
                return node
        return None

    def get_connections(self, slug: str) -> list[dict]:
        """Get all connections for a node."""
        graph = self._get_graph_dict()
        edges = graph.get("edges", [])

        connections = []
        for edge in edges:
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
