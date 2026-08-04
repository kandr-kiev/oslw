"""GraphQuery - conceptual search through knowledge graph.

Performs fuzzy matching and BFS traversal on the knowledge graph
to find relevant pages for a query.

Usage:
    from oslw.config import settings
    query = GraphQuery(wiki_root=settings.wiki_root)
    results = query.search("transformers", depth=2, limit=5)
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.graph.generator import GraphGenerator

logger = get_logger("domain.graph.query")


@dataclass
class QueryResult:
    """Result of a graph query.

    Attributes:
        node_id: Node identifier
        label: Human-readable label
        type: Node type
        score: Relevance score (0.0-1.0)
        distance: BFS distance from query node
    """

    node_id: str
    label: str
    type: str
    score: float = 0.0
    distance: int = 0


class GraphQuery:
    """Conceptual search through knowledge graph.

    Algorithm:
    1. Load graph-from-wiki.json
    2. Fuzzy match query against node labels
    3. BFS traversal from matched nodes (depth=N)
    4. Score nodes by relevance (direct match > connected > distant)
    5. Return top-K results

    Usage:
        from oslw.config import settings
        query = GraphQuery(wiki_root=settings.wiki_root)
        results = query.search("RAG", depth=2, limit=5)
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize GraphQuery.

        Args:
            wiki_root: Path to wiki root directory (from Settings, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)
        self.graph_path = self.wiki_root / "graph-from-wiki.json"
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self._adjacency: dict[str, list[str]] = {}

    def load_graph(self) -> None:
        """Load graph from graph-from-wiki.json.

        Raises:
            FileNotFoundError: If graph file doesn't exist
        """
        if not self.graph_path.exists():
            # Generate graph if not exists
            logger.info("Graph not found, generating...")
            generator = GraphGenerator(self.wiki_root)
            graph_data = generator.generate()
            self._load_from_data(graph_data)
        else:
            text = self.graph_path.read_text(encoding="utf-8")
            graph_data = json.loads(text)
            self._load_from_data(graph_data)

    def _load_from_data(self, data: dict) -> None:
        """Load graph from dictionary data.

        Args:
            data: Graph data with nodes and edges
        """
        import json

        self.nodes = {}
        self.edges = []
        self._adjacency = {}

        for node in data.get("nodes", []):
            node_id = node.get("id", "")
            self.nodes[node_id] = node
            if node_id not in self._adjacency:
                self._adjacency[node_id] = []

        for edge in data.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            self.edges.append(edge)
            if source in self._adjacency:
                self._adjacency[source].append(target)

        logger.info("Loaded graph: %d nodes, %d edges", len(self.nodes), len(self.edges))

    def search(
        self,
        query: str,
        depth: int = 2,
        limit: int = 5,
    ) -> list[QueryResult]:
        """Search knowledge graph for relevant nodes.

        Args:
            query: Search query
            depth: BFS traversal depth
            limit: Maximum results to return

        Returns:
            List of QueryResult sorted by relevance score
        """
        self.load_graph()

        # Fuzzy match query against node labels
        candidates = self._fuzzy_match(query)

        if not candidates:
            logger.warning("No candidates found for query: %s", query)
            return []

        # BFS from candidates
        results = self._bfs_traversal(candidates, depth)

        # Score and sort
        scored = self._score_results(results, candidates)

        # Return top-K
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:limit]

    def _fuzzy_match(self, query: str) -> list[str]:
        """Find nodes matching the query using fuzzy matching.

        Args:
            query: Search query

        Returns:
            List of matching node IDs
        """
        query_lower = query.lower().strip()
        matches = []

        for node_id, node_data in self.nodes.items():
            label = node_data.get("label", "").lower()
            node_type = node_data.get("type", "")

            # Exact match
            if query_lower == label:
                matches.append(node_id)
                continue

            # Word boundary match
            words = query_lower.split()
            if all(any(w in label for w in words) for w in words):
                matches.append(node_id)
                continue

            # Partial match (query is substring of label)
            if query_lower in label:
                matches.append(node_id)
                continue

            # Slug match (hyphenated words)
            slug_words = node_id.replace("-", " ").split()
            if all(any(w in sw for w in words for sw in slug_words) for w in words):
                matches.append(node_id)

        logger.info("Fuzzy match found %d candidates for '%s'", len(matches), query)
        return matches

    def _bfs_traversal(
        self,
        start_nodes: list[str],
        depth: int,
    ) -> dict[str, int]:
        """Perform BFS traversal from start nodes.

        Args:
            start_nodes: Starting node IDs
            depth: Maximum traversal depth

        Returns:
            Dictionary mapping node_id to distance
        """
        visited = {node: 0 for node in start_nodes}
        queue = deque(start_nodes)

        while queue and depth > 0:
            current = queue.popleft()
            neighbors = self._adjacency.get(current, [])

            for neighbor in neighbors:
                if neighbor not in visited:
                    visited[neighbor] = visited[current] + 1
                    queue.append(neighbor)

            depth -= 1

        return visited

    def _score_results(
        self,
        visited: dict[str, int],
        candidates: list[str],
    ) -> list[QueryResult]:
        """Score and convert visited nodes to QueryResults.

        Args:
            visited: Dictionary mapping node_id to distance
            candidates: Original candidate node IDs

        Returns:
            List of QueryResult with scores
        """
        results = []

        for node_id, distance in visited.items():
            node_data = self.nodes.get(node_id, {})
            label = node_data.get("label", node_id)
            node_type = node_data.get("type", "wiki")

            # Score: direct match = 1.0, each hop = -0.2
            if node_id in candidates:
                score = 1.0
            else:
                score = max(0.0, 1.0 - (distance * 0.2))

            results.append(QueryResult(
                node_id=node_id,
                label=label,
                type=node_type,
                score=score,
                distance=distance,
            ))

        return results

    def find_backlinks(self, node_id: str) -> list[str]:
        """Find all pages that link to a specific node.

        Args:
            node_id: Target node ID

        Returns:
            List of source node IDs that link to target
        """
        self.load_graph()
        backlinks = []

        for edge in self.edges:
            if edge.get("target") == node_id:
                backlinks.append(edge.get("source", ""))

        return backlinks

    def get_neighbors(self, node_id: str, direction: str = "out") -> list[str]:
        """Get neighboring nodes.

        Args:
            node_id: Node ID
            direction: "out" for outgoing, "in" for incoming

        Returns:
            List of neighbor node IDs
        """
        self.load_graph()
        neighbors = []

        if direction == "out":
            neighbors = self._adjacency.get(node_id, [])
        elif direction == "in":
            for edge in self.edges:
                if edge.get("target") == node_id:
                    neighbors.append(edge.get("source", ""))

        return neighbors
