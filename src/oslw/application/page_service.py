"""PageService — business logic for wiki page operations.

Orchestrates FileManager and domain models to provide
complete page lifecycle management.

Usage:
    from oslw.config import settings
    from oslw.application import PageService

    service = PageService(wiki_root=settings.wiki_root)
    page = service.get_page("transformers-architecture")
    pages = service.list_pages(type="concept", limit=50)
    created = service.create_page(title="New Page", content="# Content")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.wiki.page import WikiPage
from oslw.infrastructure.database import FileManager
from oslw.core.exceptions import PageNotFoundError, ValidationError

logger = get_logger("application.page_service")


@dataclass
class PageListResult:
    """Result of listing wiki pages.

    Attributes:
        pages: List of wiki pages
        total: Total number of pages (before pagination)
        limit: Applied limit
        offset: Applied offset
    """

    pages: list[WikiPage]
    total: int = 0
    limit: int = 50
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Whether there are more pages after this batch."""
        return (self.offset + self.limit) < self.total


class PageService:
    """Wiki page CRUD service.

    Provides complete page lifecycle management:
    - List pages with filtering and pagination
    - Get single page by slug or path
    - Create new pages
    - Update existing pages
    - Delete pages

    Usage:
        service = PageService(wiki_root=Path("./wiki"))
        page = service.get_page("transformers-architecture")
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize PageService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))

    def get_page(self, slug: str) -> WikiPage:
        """Get a wiki page by slug.

        Args:
            slug: Page slug

        Returns:
            WikiPage if found

        Raises:
            PageNotFoundError: If page doesn't exist
        """
        page_meta = self.file_manager.read_page(slug)
        if not page_meta:
            raise PageNotFoundError(slug=slug)

        return WikiPage.from_meta(page_meta)

    def get_page_by_path(self, file_path: str | Path) -> WikiPage:
        """Get a wiki page by file path.

        Args:
            file_path: Path to the markdown file

        Returns:
            WikiPage if found

        Raises:
            PageNotFoundError: If file doesn't exist or can't be parsed
        """
        page_meta = self.file_manager.read_page_by_path(file_path)
        if not page_meta:
            raise PageNotFoundError(slug=Path(file_path).stem)

        return WikiPage.from_meta(page_meta)

    def list_pages(
        self,
        category: Optional[str] = None,
        type_filter: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PageListResult:
        """List wiki pages with filtering and pagination.

        Args:
            category: Optional category filter (concepts, comparisons, etc.)
            type_filter: Optional page type filter
            tag: Optional tag filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            PageListResult with filtered pages
        """
        all_pages = self.file_manager.list_wiki_pages(category=category)

        # Apply filters
        filtered = all_pages
        if type_filter:
            filtered = [p for p in filtered if p.type == type_filter]
        if tag:
            filtered = [p for p in filtered if tag in p.tags]

        total = len(filtered)

        # Apply pagination
        paginated = filtered[offset:offset + limit]

        # Convert to WikiPage objects
        pages = [WikiPage.from_meta(p) for p in paginated]

        return PageListResult(
            pages=pages,
            total=total,
            limit=limit,
            offset=offset,
        )

    def create_page(
        self,
        title: str,
        content: str,
        slug: Optional[str] = None,
        page_type: str = "concept",
        tags: Optional[list[str]] = None,
        sources: Optional[list[str]] = None,
    ) -> WikiPage:
        """Create a new wiki page.

        Args:
            title: Page title
            content: Markdown content
            slug: Optional slug (generated from title if not provided)
            page_type: Page type (concept, comparison, etc.)
            tags: List of tags
            sources: List of source URLs

        Returns:
            Created WikiPage

        Raises:
            ValidationError: If title is empty or slug already exists
        """
        if not title.strip():
            raise ValidationError("Title cannot be empty")

        # Generate slug if not provided
        if not slug:
            slug = WikiPage.generate_slug(title)

        # Check if slug already exists
        existing = self.file_manager.read_page(slug)
        if existing:
            raise ValidationError(f"Page with slug '{slug}' already exists")

        # Create page meta
        from oslw.domain.wiki.page import PageMeta
        page_meta = PageMeta(
            slug=slug,
            title=title,
            description="",
            type=page_type,
            tags=tags or [],
            sources=sources or [],
            content=content,
        )

        # Write page
        written_path = self.file_manager.write_page(page_meta)

        # Reload to get full metadata
        created_page = self.get_page(slug)
        logger.info("Created page: %s -> %s", slug, written_path)

        return created_page

    def update_page(
        self,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> WikiPage:
        """Update an existing wiki page.

        Args:
            slug: Page slug
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)

        Returns:
            Updated WikiPage

        Raises:
            PageNotFoundError: If page doesn't exist
        """
        page = self.get_page(slug)

        # Apply updates
        if title is not None:
            page.title = title
        if content is not None:
            page.content = content
        if tags is not None:
            page.tags = tags

        # Write updated page
        page_meta = page.to_meta()
        written_path = self.file_manager.write_page(page_meta)

        # Reload to get updated metadata
        updated_page = self.get_page(slug)
        logger.info("Updated page: %s -> %s", slug, written_path)

        return updated_page

    def delete_page(self, slug: str) -> bool:
        """Delete a wiki page.

        Args:
            slug: Page slug to delete

        Returns:
            True if deleted, False if not found

        Raises:
            PageNotFoundError: If page doesn't exist (when strict=True)
        """
        # Verify page exists
        page = self.get_page(slug)

        # Delete
        deleted = self.file_manager.delete_page(slug)

        if deleted:
            logger.info("Deleted page: %s", slug)
        else:
            raise PageNotFoundError(slug=slug)

        return deleted

    def page_exists(self, slug: str) -> bool:
        """Check if a page exists.

        Args:
            slug: Page slug

        Returns:
            True if page exists
        """
        return self.file_manager.read_page(slug) is not None

    def get_page_count(self) -> int:
        """Get total number of wiki pages.

        Returns:
            Number of wiki pages
        """
        return self.file_manager.get_page_count()
