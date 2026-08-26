"""FileManager - file-based storage layer for OSLW.

Provides:
- Direct file operations on wiki/, raw/ directories
- Index.md management
- Frontmatter read/write
- File discovery and listing

This is the ONLY data access layer — no SQL, no separate database.
All data lives in markdown files on disk.

Usage:
    from oslw.config import settings
    fm = FileManager(wiki_root=settings.wiki_root)
    pages = fm.list_wiki_pages()
    page = fm.read_page("transformers-architecture")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.core.exceptions import FileManagerError
from oslw.utils.slug import norm_name

logger = get_logger("infrastructure.database")


@dataclass
class PageMeta:
    """Metadata extracted from a wiki page file.

    Attributes:
        slug: Page slug
        title: Page title
        description: Page description
        type: Page type (concept, comparison, etc.)
        tags: List of tags
        sources: List of source URLs
        sha256: SHA256 hash of page content
        created: Creation timestamp
        updated: Last modification timestamp
        path: Full path to the file
        content: Raw markdown content (without frontmatter)
        raw_content: Full file content (with frontmatter)
    """

    slug: str
    title: str
    description: str = ""
    type: str = "concept"
    tags: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    sha256: str = ""
    created: str = ""
    updated: str = ""
    path: Path = field(default_factory=Path)
    content: str = ""
    raw_content: str = ""


class FileManager:
    """File-based storage layer for OSLW.

    Provides direct file operations on wiki/, raw/ directories.
    No SQL, no separate database — all data lives in markdown files.

    Usage:
        from oslw.config import settings
        fm = FileManager(wiki_root=settings.wiki_root)
        pages = fm.list_wiki_pages()
        page = fm.read_page("transformers-architecture")
    """

    # Frontmatter field patterns
    SLUG_PATTERN = re.compile(r'^slug:\s*(\S+)', re.MULTILINE)
    TITLE_PATTERN = re.compile(r'^title:\s*(.+)', re.MULTILINE)
    TYPE_PATTERN = re.compile(r'^type:\s*(\S+)', re.MULTILINE)
    TAGS_PATTERN = re.compile(r'^tags:\s*\[(.+)\]', re.MULTILINE)
    SOURCES_PATTERN = re.compile(r'^sources:\s*\[(.+)\]', re.MULTILINE)
    SHA256_PATTERN = re.compile(r'^sha256:\s*(\S+)', re.MULTILINE)
    CREATED_PATTERN = re.compile(r'^created:\s*(.+)', re.MULTILINE)
    UPDATED_PATTERN = re.compile(r'^updated:\s*(.+)', re.MULTILINE)

    # Index entry pattern
    INDEX_ENTRY_PATTERN = re.compile(r'^###\s+(\S+)\s+\[([^\]]+)\](?:\s+(.*))?$')

    def __init__(self, wiki_root: str | Path):
        """Initialize FileManager.

        Args:
            wiki_root: Path to wiki root directory (from Settings, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)
        self.wiki_dir = self.wiki_root
        self.raw_dir = self.wiki_root / "raw"
        self.index_path = self.wiki_dir / "index.md"

    def read_page(self, slug: str) -> Optional[PageMeta]:
        """Read a wiki page by slug.

        Args:
            slug: Page slug

        Returns:
            PageMeta if found, None otherwise
        """
        # Search for the file
        file_path = self._find_page_file(slug)
        if not file_path:
            logger.warning("Сторінку не знайдено: %s", slug)
            return None

        return self._parse_page(file_path)

    def read_page_by_path(self, file_path: str | Path) -> Optional[PageMeta]:
        """Read a wiki page by file path.

        Args:
            file_path: Path to the markdown file

        Returns:
            PageMeta if found, None otherwise
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning("File not found: %s", path)
            return None

        return self._parse_page(path)

    def _parse_page(self, file_path: Path) -> PageMeta:
        """Parse a markdown file into PageMeta.

        Args:
            file_path: Path to the markdown file

        Returns:
            PageMeta with extracted metadata
        """
        raw_content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter
        frontmatter = {}
        content = raw_content

        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                content = parts[2]

                # Parse frontmatter fields
                for pattern, field_name in [
                    (self.SLUG_PATTERN, "slug"),
                    (self.TITLE_PATTERN, "title"),
                    (self.TYPE_PATTERN, "type"),
                    (self.SHA256_PATTERN, "sha256"),
                    (self.CREATED_PATTERN, "created"),
                    (self.UPDATED_PATTERN, "updated"),
                ]:
                    match = pattern.search(frontmatter_text)
                    if match:
                        frontmatter[field_name] = match.group(1).strip()

                # Parse tags
                tags_match = self.TAGS_PATTERN.search(frontmatter_text)
                if tags_match:
                    frontmatter["tags"] = [
                        t.strip() for t in tags_match.group(1).split(",")
                    ]

                # Parse sources
                sources_match = self.SOURCES_PATTERN.search(frontmatter_text)
                if sources_match:
                    frontmatter["sources"] = [
                        s.strip() for s in sources_match.group(1).split(",")
                    ]

        slug = frontmatter.get("slug", file_path.stem)
        title = frontmatter.get("title", slug.replace("-", " ").title())
        page_type = frontmatter.get("type", "concept")

        return PageMeta(
            slug=slug,
            title=title,
            description="",
            type=page_type,
            tags=frontmatter.get("tags", []),
            sources=frontmatter.get("sources", []),
            sha256=frontmatter.get("sha256", ""),
            created=frontmatter.get("created", ""),
            updated=frontmatter.get("updated", ""),
            path=file_path,
            content=content,
            raw_content=raw_content,
        )

    def _find_page_file(self, slug: str) -> Optional[Path]:
        """Find the file for a given slug.

        Args:
            slug: Page slug

        Returns:
            Path to the file, or None
        """
        # Search in wiki subdirectories
        if not self.wiki_dir.exists():
            return None

        # index.md is a special page addressed by slug "index"
        if slug == "index":
            idx = self.wiki_dir / "index.md"
            return idx if idx.exists() else None

        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name in ("SCHEMA.md",):
                continue

            # Check if filename matches slug
            if md_file.stem == slug:
                return md_file

            # Check if frontmatter slug matches
            try:
                raw = md_file.read_text(encoding="utf-8")
                match = self.SLUG_PATTERN.search(raw)
                if match and match.group(1) == slug:
                    return md_file
            except Exception:
                continue

        return None

    def list_wiki_pages(self, category: Optional[str] = None) -> list[PageMeta]:
        """List all wiki pages.

        Args:
            category: Optional category filter (concept, comparisons, etc.)

        Returns:
            List of PageMeta for all pages
        """
        pages = []

        if not self.wiki_dir.exists():
            return pages

        search_dirs = [self.wiki_dir]
        if category:
            category_path = self.wiki_dir / category
            if category_path.exists():
                search_dirs = [category_path]

        for md_file in search_dirs:
            for file in md_file.rglob("*.md"):
                if file.name in ("index.md", "SCHEMA.md"):
                    continue
                try:
                    page = self._parse_page(file)
                    pages.append(page)
                except Exception as e:
                    logger.error("Error parsing %s: %s", file, e)

        logger.info("Listed %d wiki pages", len(pages))
        return pages

    def list_raw_articles(self) -> list[Path]:
        """List all raw articles.

        Returns:
            List of paths to raw article files
        """
        articles = []

        if not self.raw_dir.exists():
            return articles

        for md_file in self.raw_dir.rglob("*.md"):
            articles.append(md_file)

        logger.info("Список %d сирних статей", len(articles))
        return articles

    def write_page(self, page: PageMeta) -> Path:
        """Write a wiki page.

        Deduplication (Layer 2): a normalized slug is unique across ALL category
        directories. Before writing, the manager looks up any existing page with
        the same normalized slug (regardless of which category it lives in). If an
        identical page already exists (same SHA256 body) nothing is written and the
        existing path is returned. If a page with the same slug but different
        content exists, it is updated in place at its CURRENT location — never
        duplicated into another category.

        Args:
            page: PageMeta with content to write

        Returns:
            Path to the written file
        """
        import hashlib

        # Normalize the slug so that punctuation/whitespace variants of the same
        # concept collapse to ONE filename. This is what makes "role:" and "role-"
        # (and identical content across categories) resolve to a single file.
        safe_slug = norm_name(page.slug) or page.slug

        # Lookup existing page by normalized slug across every category
        existing_path = self._find_page_file(safe_slug)
        if existing_path and existing_path.exists():
            existing = self._parse_page(existing_path)
            new_hash = hashlib.sha256(page.content.encode("utf-8")).hexdigest()
            # Identical content -> nothing to do, return existing location
            if existing.sha256 == new_hash or existing.content == page.content:
                logger.info("Дублікат (ідентичний вміст), пропуск: %s", safe_slug)
                return existing_path
            # Same slug, different content -> overwrite in place (no new category)
            file_path = existing_path
        else:
            # Determine category directory (Layer 2 types)
            category = page.type
            category_dir = self.wiki_dir / category
            # Generate filename from the canonical slug
            filename = f"{safe_slug}.md"
            file_path = category_dir / filename

        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate frontmatter (store the canonical slug)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        content_hash = hashlib.sha256(page.content.encode("utf-8")).hexdigest()
        lines = [
            "---",
            f"title: {page.title}",
            f"slug: {safe_slug}",
            f"type: {page.type}",
            f"tags: [{', '.join(page.tags)}]",
            f"sha256: {content_hash}",
            f"created: {page.created or now}",
            f"updated: {now}",
        ]

        if page.sources:
            lines.append(f"sources: [{', '.join(page.sources)}]")

        lines.append("---")

        # Write file
        content = "\n".join(lines) + "\n\n" + page.content
        file_path.write_text(content, encoding="utf-8")

        logger.info("Wrote page: %s -> %s", page.slug, file_path)
        return file_path

    def delete_page(self, slug: str) -> bool:
        """Delete a wiki page.

        Args:
            slug: Page slug to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self._find_page_file(slug)
        if not file_path:
            logger.warning("Page not found for deletion: %s", slug)
            return False

        file_path.unlink()
        logger.info("Видалено сторінку: %s -> %s", slug, file_path)

        # Update index
        self._remove_from_index(slug)

        return True

    def update_index(self) -> None:
        """Rebuild the wiki index from all pages.

        This scans all wiki pages and updates index.md.
        """
        if not self.wiki_dir.exists():
            logger.warning("Директорію wiki не знайдено: %s", self.wiki_dir)
            return

        entries = []

        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue

            try:
                raw = md_file.read_text(encoding="utf-8")
                slug_match = self.SLUG_PATTERN.search(raw)
                title_match = self.TITLE_PATTERN.search(raw)

                if slug_match:
                    slug = slug_match.group(1)
                    title = title_match.group(1).strip() if title_match else slug
                    rel_path = str(md_file.relative_to(self.wiki_root))
                    entries.append((slug, rel_path, title))
            except Exception as e:
                logger.error("Error reading %s: %s", md_file, e)

        # Sort by slug
        entries.sort(key=lambda x: x[0])

        # Write index
        lines = ["# LLM-Wiki Index", ""]
        for slug, path, title in entries:
            lines.append(f"### {slug} [{path}] {title}")

        lines.append("")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text("\n".join(lines), encoding="utf-8")

        logger.info("Updated index with %d entries", len(entries))

    def _remove_from_index(self, slug: str) -> None:
        """Remove a page entry from index.md.

        Args:
            slug: Page slug to remove
        """
        if not self.index_path.exists():
            return

        text = self.index_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        filtered = [
            line for line in lines
            if not self.INDEX_ENTRY_PATTERN.match(line.strip())
            or self.INDEX_ENTRY_PATTERN.match(line.strip()).group(1) != slug
        ]

        self.index_path.write_text("\n".join(filtered), encoding="utf-8")
        logger.info("Removed %s from index", slug)

    def get_page_count(self) -> int:
        """Get the total number of wiki pages.

        Returns:
            Number of wiki pages (excluding index.md and SCHEMA.md)
        """
        if not self.wiki_dir.exists():
            return 0

        count = sum(1 for _ in self.wiki_dir.rglob("*.md"))
        # Subtract index.md and SCHEMA.md if they exist
        if self.index_path.exists():
            count -= 1
        schema_path = self.wiki_dir / "schema" / "SCHEMA.md"
        if schema_path.exists():
            count -= 1
        return max(0, count)
