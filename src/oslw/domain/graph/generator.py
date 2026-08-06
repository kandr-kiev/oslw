"""GraphGenerator - generates knowledge graph from wiki wikilinks.

Converts wiki/ with [[wikilinks]] into graph.json format:
{
    "nodes": [{"id": "...", "label": "...", "type": "..."}],
    "edges": [{"source": "...", "target": "...", "label": "..."}]
}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.core.exceptions import GraphGenerationError

logger = get_logger("domain.graph.generator")


@dataclass
class GraphNode:
    """Single node in the knowledge graph.

    Attributes:
        id: Unique node identifier (slug)
        label: Human-readable label
        type: Node type (concept, comparison, etc.)
    """

    id: str
    label: str
    type: str = "wiki"


@dataclass
class GraphEdge:
    """Single edge in the knowledge graph.

    Attributes:
        source: Source node ID
        target: Target node ID
        label: Edge label (optional)
    """

    source: str
    target: str
    label: str = ""


class GraphGenerator:
    """Generate knowledge graph from wiki wikilinks.

    Reads wiki/ directory, extracts [[wikilinks]], and builds
    a directed graph of nodes and edges.

    Usage:
        from oslw.config import settings
        generator = GraphGenerator(wiki_root=settings.wiki_root)
        graph = generator.generate()
        graph.to_json("graph-from-wiki.json")
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize GraphGenerator.

        Args:
            wiki_root: Path to wiki root directory (from Settings, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)
        self.wiki_dir = self.wiki_root / "wiki"
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._cache_mtime: float = 0
        self._cache_valid: bool = False

    def generate(self, force: bool = False) -> dict:
        """Generate the knowledge graph.

        Args:
            force: If True, regenerate from scratch. If False, load cached graph if available and valid.

        Returns:
            Dictionary with nodes and edges

        Raises:
            GraphGenerationError: If wiki directory not found
        """
        if not self.wiki_dir.exists():
            raise GraphGenerationError(f"Wiki directory not found: {self.wiki_dir}")

        # Check if cache is valid (not forced + cache exists + wiki files unchanged)
        if not force and self._cache_valid:
            cache_path = self.wiki_root / "graph-from-wiki.json"
            if cache_path.exists():
                logger.info("Using valid cached graph: %d nodes, %d edges",
                           len(self.nodes), len(self.edges))
                return {
                    "nodes": [n.__dict__ for n in self.nodes.values()],
                    "edges": [e.__dict__ for e in self.edges],
                }

        # Load cached graph if available and not forcing regeneration
        cache_path = self.wiki_root / "graph-from-wiki.json"
        if not force and cache_path.exists():
            try:
                graph_data = json.loads(cache_path.read_text(encoding="utf-8"))
                nodes_data = graph_data.get("nodes", [])
                if nodes_data:
                    logger.info("Loaded cached graph: %d nodes, %d edges",
                               len(nodes_data), len(graph_data.get("edges", [])))
                    # Rebuild internal state from cache
                    self.nodes = {
                        n["id"]: GraphNode(id=n["id"], label=n["label"], type=n.get("type", "wiki"))
                        for n in nodes_data
                    }
                    self.edges = [
                        GraphEdge(source=e["source"], target=e["target"], label=e.get("label", ""))
                        for e in graph_data.get("edges", [])
                    ]
                    self._cache_valid = True
                    self._cache_mtime = cache_path.stat().st_mtime
                    return {
                        "nodes": [n.__dict__ for n in self.nodes.values()],
                        "edges": [e.__dict__ for e in self.edges],
                    }
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load cached graph: %s, regenerating", e)

        # Full regeneration
        self.nodes = {}
        self.edges = []
        self._cache_valid = False

        # Process all wiki pages
        for md_file in self.wiki_dir.rglob("*.md"):
            # Skip index.md and SCHEMA.md
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue

            # Read file and extract wikilinks
            text = md_file.read_text(encoding="utf-8")

            # Extract slug from frontmatter or filename
            slug = self._extract_slug(text, md_file)
            if not slug:
                continue

            # Add node
            if slug not in self.nodes:
                title = self._extract_title(text)
                page_type = self._extract_type(text)
                self.nodes[slug] = GraphNode(
                    id=slug,
                    label=title or slug,
                    type=page_type,
                )

            # Extract wikilinks (edges)
            links = re.findall(r'\[\[([^\]]+)\]\]', text)
            for link in links:
                # Skip internal links and non-slugs
                if link.startswith("#") or link.startswith("/"):
                    continue
                if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', link):
                    continue

                # Add target node if not exists
                if link not in self.nodes:
                    self.nodes[link] = GraphNode(id=link, label=link, type="wiki")

                # Add edge if not duplicate
                if not any(e.source == slug and e.target == link for e in self.edges):
                    self.edges.append(GraphEdge(source=slug, target=link))

        logger.info("Generated graph: %d nodes, %d edges", len(self.nodes), len(self.edges))

        return {
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
        }

    def to_json(self, output_path: str | Path) -> None:
        """Save graph to JSON file.

        Args:
            output_path: Path to output file
        """
        graph = self.generate()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved graph to %s", path)

    def _extract_slug(self, text: str, file_path: Path) -> Optional[str]:
        """Extract slug from frontmatter or filename.

        Args:
            text: File content
            file_path: Path to file

        Returns:
            Slug or None
        """
        # Try frontmatter
        slug_match = re.search(r'^slug:\s*(\S+)', text, re.MULTILINE)
        if slug_match:
            return slug_match.group(1)

        # Fall back to filename
        stem = file_path.stem
        if stem and stem != "index":
            return stem

        return None

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from frontmatter.

        Args:
            text: File content

        Returns:
            Title or None
        """
        title_match = re.search(r'^title:\s*(.+)', text, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        return None

    def _extract_type(self, text: str) -> str:
        """Extract page type from frontmatter.

        Args:
            text: File content

        Returns:
            Page type (default: "concept")
        """
        type_match = re.search(r'^type:\s*(\S+)', text, re.MULTILINE)
        if type_match:
            return type_match.group(1)
        return "concept"
