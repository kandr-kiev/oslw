"""IndexService — business logic for wiki index management.

Orchestrates WikiIndex and FileManager to provide
complete index lifecycle management.

Usage:
    from oslw.config import settings
    from oslw.application import IndexService

    service = IndexService(wiki_root=settings.wiki_root)
    index = await service.get_index()
    await service.rebuild_index()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.wiki.index import WikiIndex, IndexEntry
from oslw.infrastructure.database import FileManager
from oslw.core.exceptions import IndexError

logger = get_logger("application.index_service")


@dataclass
class IndexStats:
    """Statistics about the wiki index.

    Attributes:
        total_entries: Total number of index entries
        total_pages: Total number of wiki pages
        categories: Number of categories
        last_updated: Last index update timestamp
    """

    total_entries: int = 0
    total_pages: int = 0
    categories: int = 0
    last_updated: Optional[str] = None


class IndexService:
    """Wiki index management service.

    Provides:
    - Load index from index.md
    - Rebuild index from all wiki pages
    - Search index entries
    - Get index statistics

    Usage:
        service = IndexService(wiki_root=Path("./wiki"))
        index = await service.get_index()
        stats = await service.get_stats()
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize IndexService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.index = WikiIndex(wiki_root=Path(wiki_root))

    async def get_index(self) -> WikiIndex:
        """Load and return the wiki index.

        Returns:
            WikiIndex with all entries loaded

        Raises:
            IndexError: If index.md doesn't exist or can't be parsed
        """
        if not self.index.load():
            logger.warning("Index not found, returning empty index")
            return self.index

        return self.index

    async def rebuild_index(self) -> int:
        """Rebuild the wiki index from all pages.

        Scans all wiki pages and updates index.md.

        Returns:
            Number of entries in rebuilt index
        """
        self.file_manager.update_index()
        loaded = self.index.load()

        if not loaded:
            raise IndexError("Failed to rebuild index")

        logger.info("Rebuilt index with %d entries", len(self.index.entries))
        return len(self.index.entries)

    async def search_index(self, query: str) -> list[IndexEntry]:
        """Search index entries by query.

        Args:
            query: Search query string

        Returns:
            List of matching IndexEntry objects
        """
        if not self.index.entries:
            await self.get_index()

        results = []
        query_lower = query.lower()

        for entry in self.index.entries.values():
            if (query_lower in entry.slug.lower() or
                query_lower in entry.title.lower() or
                query_lower in entry.description.lower()):
                results.append(entry)

        logger.info("Search '%s' returned %d results", query, len(results))
        return results

    async def get_stats(self) -> IndexStats:
        """Get index statistics.

        Returns:
            IndexStats with current statistics
        """
        index = await self.get_index()
        pages = self.file_manager.list_wiki_pages()

        # Count categories
        categories = set()
        for page in pages:
            categories.add(page.type)

        return IndexStats(
            total_entries=len(index.entries),
            total_pages=len(pages),
            categories=len(categories),
            last_updated=index.updated_at,
        )

    async def get_entry(self, slug: str) -> Optional[IndexEntry]:
        """Get a single index entry by slug.

        Args:
            slug: Page slug

        Returns:
            IndexEntry if found, None otherwise
        """
        if not self.index.entries:
            await self.get_index()

        return self.index.entries.get(slug)
