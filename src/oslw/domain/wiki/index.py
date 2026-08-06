"""WikiIndex - manages wiki/index.md for page discovery.

The index is the single source of truth for wiki page discovery.
It maps slugs to file paths and provides O(1) lookup.

Format:
    ### slug [path/to/file.md]
    [optional description]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.core.exceptions import OslwError

logger = get_logger("domain.wiki.index")


@dataclass
class IndexEntry:
    """Single entry in the wiki index.

    Attributes:
        slug: Page slug (from frontmatter or filename)
        path: Relative path to the page file
        description: Optional description (from frontmatter or first line)
    """

    slug: str
    path: str
    description: str = ""


class WikiIndexError(OslwError):
    """Index-related errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class WikiIndex:
    """Manages wiki/index.md for page discovery.

    Provides:
    - Parsing index.md into IndexEntry objects
    - Adding/removing/updating entries
    - Saving index back to disk
    - Lookup by slug or path

    Usage:
        index = WikiIndex(wiki_root=Path("./wiki"))
        index.load()  # Load from index.md
        index.add_entry("transformers-architecture", "wiki/concept/transformers-architecture.md")
        index.save()  # Save changes
    """

    # Regex for parsing index entries: ### slug [path]
    ENTRY_PATTERN = re.compile(r'^###\s+(\S+)\s+\[([^\]]+)\](?:\s+(.*))?$')

    def __init__(self, wiki_root: str | Path):
        """Initialize WikiIndex.

        Args:
            wiki_root: Path to wiki root directory (configurable, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)
        self.index_path = self.wiki_root / "wiki" / "index.md"
        self.entries: dict[str, IndexEntry] = {}
        self._raw_lines: list[str] = []

    def load(self) -> None:
        """Load index from index.md file.

        Raises:
            WikiIndexError: If index file cannot be read
        """
        if not self.index_path.exists():
            logger.warning("Index file does not exist: %s", self.index_path)
            self.entries = {}
            return

        try:
            text = self.index_path.read_text(encoding="utf-8")
            self._parse(text)
            logger.info("Loaded %d entries from index", len(self.entries))
        except Exception as e:
            raise WikiIndexError(f"Failed to load index: {e}")

    def _parse(self, text: str) -> None:
        """Parse index.md text into entries.

        Args:
            text: Raw index.md content
        """
        self.entries = {}
        self._raw_lines = text.splitlines()

        for line in self._raw_lines:
            match = self.ENTRY_PATTERN.match(line.strip())
            if match:
                slug = match.group(1)
                path = match.group(2)
                description = match.group(3) or ""
                self.entries[slug] = IndexEntry(
                    slug=slug,
                    path=path,
                    description=description.strip(),
                )

    def save(self) -> None:
        """Save index entries to index.md file.

        Raises:
            WikiIndexError: If index file cannot be written
        """
        try:
            lines = ["# LLM-Wiki Index", ""]

            # Sort entries by slug for consistent output
            for slug in sorted(self.entries.keys()):
                entry = self.entries[slug]
                line = f"### {entry.slug} [{entry.path}]"
                if entry.description:
                    line += f" {entry.description}"
                lines.append(line)

            lines.append("")  # Trailing newline
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index_path.write_text("\n".join(lines), encoding="utf-8")
            logger.info("Saved %d entries to index", len(self.entries))
        except Exception as e:
            raise WikiIndexError(f"Failed to save index: {e}")

    def add_entry(self, slug: str, path: str, description: str = "") -> None:
        """Add an entry to the index.

        Args:
            slug: Page slug
            path: Relative path to the page file
            description: Optional description
        """
        self.entries[slug] = IndexEntry(slug=slug, path=path, description=description)
        logger.debug("Added entry: %s -> %s", slug, path)

    def remove_entry(self, slug: str) -> bool:
        """Remove an entry from the index.

        Args:
            slug: Page slug to remove

        Returns:
            True if entry was found and removed, False otherwise
        """
        if slug in self.entries:
            del self.entries[slug]
            logger.debug("Removed entry: %s", slug)
            return True
        return False

    def update_entry(self, slug: str, path: str, description: str = "") -> None:
        """Update an existing entry in the index.

        Args:
            slug: Page slug to update
            path: New path
            description: New description
        """
        if slug in self.entries:
            self.entries[slug] = IndexEntry(slug=slug, path=path, description=description)
            logger.debug("Updated entry: %s -> %s", slug, path)
        else:
            self.add_entry(slug, path, description)

    def get_entry(self, slug: str) -> Optional[IndexEntry]:
        """Get an entry by slug.

        Args:
            slug: Page slug

        Returns:
            IndexEntry if found, None otherwise
        """
        return self.entries.get(slug)

    def has_entry(self, slug: str) -> bool:
        """Check if an entry exists in the index.

        Args:
            slug: Page slug

        Returns:
            True if entry exists
        """
        return slug in self.entries

    def get_all_slugs(self) -> list[str]:
        """Get all slugs in the index.

        Returns:
            List of all slugs
        """
        return sorted(self.entries.keys())

    def count(self) -> int:
        """Get total number of entries.

        Returns:
            Number of entries
        """
        return len(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"WikiIndex(entries={len(self.entries)}, path={self.index_path})"
