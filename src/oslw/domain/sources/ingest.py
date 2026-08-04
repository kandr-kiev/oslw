"""Content ingestion - raw article processing pipeline.

Handles the transformation from raw content to wiki pages:
1. Fetch content from source
2. Extract title, content, metadata
3. Generate slug from title
4. Create frontmatter
5. Write to raw/ or wiki/ directory
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.core.exceptions import IngestError

logger = get_logger("domain.sources.ingest")


@dataclass
class IngestResult:
    """Result of content ingestion.

    Attributes:
        success: Whether ingestion was successful
        slug: Generated slug for the article
        title: Article title
        raw_path: Path where raw file was saved
        wiki_path: Path where wiki page was saved (if converted)
        errors: List of errors during ingestion
        warnings: List of warnings during ingestion
    """

    success: bool = True
    slug: str = ""
    title: str = ""
    raw_path: Optional[Path] = None
    wiki_path: Optional[Path] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ContentIngestor:
    """Content ingestion pipeline.

    Handles:
    - Raw article ingestion
    - Frontmatter generation
    - Slug generation
    - File writing

    Usage:
        ingestor = ContentIngestor(wiki_root="/workspace/llm-wiki")
        result = ingestor.ingest(
            title="Transformer Architecture",
            content="# Transformer Architecture\n\n...",
            source_url="https://example.com/article",
            tags=["transformers", "architecture"],
        )
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize ContentIngestor.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.wiki_root = Path(wiki_root)
        self.raw_dir = self.wiki_root / "raw" / "articles"
        self.wiki_dir = self.wiki_root / "wiki"

    def ingest(
        self,
        title: str,
        content: str,
        source_url: str = "",
        tags: list[str] = None,
        source_name: str = "",
    ) -> IngestResult:
        """Ingest content into the wiki.

        Args:
            title: Article title
            content: Markdown content
            source_url: Source URL (optional)
            tags: List of tags (optional)
            source_name: Source name for tracking (optional)

        Returns:
            IngestResult with success status and paths
        """
        tags = tags or []
        result = IngestResult()

        try:
            # Generate slug from title
            slug = self._generate_slug(title)
            result.slug = slug
            result.title = title

            # Generate frontmatter
            frontmatter = self._generate_frontmatter(
                title=title,
                slug=slug,
                tags=tags,
                source_url=source_url,
                source_name=source_name,
            )

            # Write raw file
            raw_filename = f"{slug}.md"
            raw_path = self.raw_dir / raw_filename
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(f"{frontmatter}\n---\n{content}", encoding="utf-8")
            result.raw_path = raw_path

            logger.info("Ingested article: %s -> %s", title, raw_path)

        except Exception as e:
            result.success = False
            result.errors.append(f"Ingestion failed: {e}")
            logger.error("Ingestion failed for '%s': %s", title, e)

        return result

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title.

        Args:
            title: Article title

        Returns:
            URL-friendly slug (e.g., "transformer-architecture")
        """
        # Lowercase
        slug = title.lower().strip()

        # Replace spaces and special chars with hyphens
        slug = slug.replace(" ", "-")
        slug = slug.replace("_", "-")

        # Remove non-alphanumeric characters (except hyphens)
        import re
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Collapse multiple hyphens
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip("-")

        # Ensure minimum length
        if len(slug) < 3:
            slug = f"page-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        return slug

    def _generate_frontmatter(
        self,
        title: str,
        slug: str,
        tags: list[str],
        source_url: str = "",
        source_name: str = "",
    ) -> str:
        """Generate YAML frontmatter for a wiki page.

        Args:
            title: Page title
            slug: Page slug
            tags: List of tags
            source_url: Source URL (optional)
            source_name: Source name (optional)

        Returns:
            YAML frontmatter string
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "---",
            f"title: {title}",
            f"slug: {slug}",
            f"type: concept",
            f"tags: [{', '.join(tags)}]",
            f"created: {now}",
            f"updated: {now}",
        ]

        if source_url:
            lines.append(f"source_url: {source_url}")
        if source_name:
            lines.append(f"source: {source_name}")

        lines.append("---")

        return "\n".join(lines)

    def cleanup_duplicates(self, dir_path: str | Path) -> list[str]:
        """Remove duplicate wiki pages (_1, _2 suffixes).

        Args:
            dir_path: Directory to clean up

        Returns:
            List of removed files
        """
        path = Path(dir_path)
        if not path.exists():
            return []

        import re
        import os

        # Find all files with _N suffix
        files = [f.name for f in path.glob("*.md")]
        base_names = {}

        for filename in files:
            match = re.match(r'^(.+)_\d+\.md$', filename)
            if match:
                base = match.group(1)
                if base not in base_names:
                    base_names[base] = []
                base_names[base].append(filename)

        removed = []
        for base, versions in base_names.items():
            # Keep the base version if it exists, otherwise keep highest _N
            base_file = f"{base}.md"
            if base_file in files:
                # Delete all _N versions
                for version in versions:
                    version_path = path / version
                    version_path.unlink()
                    removed.append(str(version_path))
                    logger.info("Removed duplicate: %s", version_path)
            else:
                # Keep highest _N, delete rest
                versions.sort(key=lambda x: int(re.search(r'_(\d+)$', x).group(1)))
                keep = versions[-1]
                for version in versions[:-1]:
                    version_path = path / version
                    version_path.unlink()
                    removed.append(str(version_path))
                    logger.info("Removed duplicate: %s", version_path)

                # Rename highest _N to base
                if keep != f"{base}.md":
                    keep_path = path / keep
                    base_path = path / f"{base}.md"
                    keep_path.rename(base_path)
                    removed.append(str(keep_path))
                    logger.info("Renamed %s -> %s", keep, base)

        return removed
