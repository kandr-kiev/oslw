"""GraphGenerator - generates knowledge graph from wiki wikilinks.

Converts wiki/ with [[wikilinks]] into graph.json format:
{
    "nodes": [{"id": "...", "label": "...", "type": "..."}],
    "edges": [{"source": "...", "target": "...", "label": "..."}]
}
"""

from __future__ import annotations

import json
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

    def generate(self) -> dict:
        """Generate the knowledge graph.

        Returns:
            Dictionary with nodes and edges

        Raises:
            GraphGenerationError: If wiki directory not found
        """
        if not self.wiki_dir.exists():
            raise GraphGenerationError(f"Wiki directory not found: {self.wiki_dir}")

        self.nodes = {}
        self.edges = []

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
            import re
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
        import re
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
        import re
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
        import re
        type_match = re.search(r'^type:\s*(\S+)', text, re.MULTILINE)
        if type_match:
            return type_match.group(1)
        return "concept"
