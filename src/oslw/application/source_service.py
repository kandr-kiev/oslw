"""SourceService — business logic for source management and content ingestion.

Orchestrates SourceConfig, ContentIngestor, SourceMonitor and FileManager to provide
complete source lifecycle management and content ingestion.

Usage:
    from oslw.config import settings
    from oslw.application import SourceService

    service = SourceService(wiki_root=settings.wiki_root)
    sources = service.list_sources()
    result = service.ingest_content(title="New Article", content="# Content")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.sources.monitor import SourceConfig, SourceType, SourceMonitor
from oslw.domain.sources.ingest import ContentIngestor, IngestResult
from oslw.infrastructure.database import FileManager

logger = get_logger("application.source_service")


@dataclass
class SourceStats:
    """Statistics about a source.

    Attributes:
        name: Source name
        type: Source type
        articles_count: Number of articles ingested
        last_checked: Last check timestamp
        last_error: Last error message (if any)
        enabled: Whether source is enabled
    """

    name: str = ""
    type: str = "rss"
    articles_count: int = 0
    last_checked: Optional[str] = None
    last_error: Optional[str] = None
    enabled: bool = True


@dataclass
class IngestionReport:
    """Report of content ingestion.

    Attributes:
        success: Whether ingestion was successful
        slug: Generated slug
        title: Article title
        raw_path: Path to raw file
        wiki_path: Path to wiki page (if converted)
        errors: List of errors
        warnings: List of warnings
    """

    success: bool = True
    slug: str = ""
    title: str = ""
    raw_path: Optional[str] = None
    wiki_path: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SourceService:
    """Source management and content ingestion service.

    Provides:
    - List and manage content sources (RSS, web, etc.)
    - Ingest content from various sources
    - Monitor sources for updates
    - Track ingestion statistics

    Usage:
        service = SourceService(wiki_root=Path("./wiki"))
        sources = service.list_sources()
        report = service.ingest_content(title="New Article", content="# Content")
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize SourceService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.ingestor = ContentIngestor(wiki_root=Path(wiki_root))
        self.monitor = SourceMonitor(wiki_root=Path(wiki_root))

    def list_sources(self) -> list[SourceStats]:
        """List all configured sources.

        Returns:
            List of SourceStats
        """
        sources = self.monitor.list_sources()
        stats = []

        for source in sources:
            stats.append(SourceStats(
                name=source.name,
                type=source.type.value,
                articles_count=source.articles_count,
                last_checked=source.last_checked,
                last_error=source.last_error,
                enabled=source.enabled,
            ))

        logger.info("Listed %d sources", len(stats))
        return stats

    def ingest_content(
        self,
        title: str,
        content: str,
        source_url: str = "",
        tags: Optional[list[str]] = None,
        source_name: str = "",
    ) -> IngestionReport:
        """Ingest content into the wiki.

        Args:
            title: Article title
            content: Markdown content
            source_url: Source URL (optional)
            tags: List of tags (optional)
            source_name: Source name (optional)

        Returns:
            IngestionReport with results
        """
        result = self.ingestor.ingest(
            title=title,
            content=content,
            source_url=source_url,
            tags=tags or [],
            source_name=source_name,
        )

        report = IngestionReport(
            success=result.success,
            slug=result.slug,
            title=result.title,
            raw_path=str(result.raw_path) if result.raw_path else None,
            wiki_path=str(result.wiki_path) if result.wiki_path else None,
            errors=result.errors,
            warnings=result.warnings,
        )

        if result.success:
            logger.info("Ingested: %s -> %s", title, result.raw_path)
        else:
            logger.error("Ingestion failed: %s - %s", title, result.errors)

        return report

    def monitor_all(self) -> dict:
        """Monitor all configured sources for updates.

        Returns:
            Dictionary with monitoring results
        """
        return self.monitor_sources()

    def monitor_sources(self) -> dict:
        """Monitor all configured sources for updates.

        Returns:
            Dictionary with monitoring results
        """
        results = self.monitor.monitor_all()

        logger.info("Monitored %d sources, found %d updates",
                   len(results),
                   sum(1 for r in results.values() if r.get("updated")))

        return results

    def get_raw_articles(self) -> list[str]:
        """List all raw articles.

        Returns:
            List of raw article file paths
        """
        articles = self.file_manager.list_raw_articles()
        paths = [str(a) for a in articles]
        logger.info("Listed %d raw articles", len(paths))
        return paths

    def cleanup_duplicates(self, directory: str = "raw/articles") -> list[str]:
        """Clean up duplicate articles.

        Args:
            directory: Directory to clean (raw/articles or wiki)

        Returns:
            List of removed files
        """
        dir_path = self.file_manager.wiki_root / directory
        removed = self.ingestor.cleanup_duplicates(dir_path)
        logger.info("Cleaned up %d duplicates in %s", len(removed), directory)
        return removed

    def add_source(
        self,
        name: str,
        source_type: str,
        url: str,
        interval_hours: int = 6,
        enabled: bool = True,
        tags: Optional[list[str]] = None,
    ) -> SourceConfig:
        """Add a new content source.

        Args:
            name: Source name
            source_type: Source type (rss, web, api)
            url: Source URL
            interval_hours: Check interval in hours
            enabled: Whether source is enabled
            tags: List of tags

        Returns:
            Created SourceConfig
        """
        try:
            st = SourceType(source_type)
        except ValueError:
            raise ValueError(f"Invalid source type: {source_type}")

        source = SourceConfig(
            name=name,
            type=st,
            url=url,
            interval_hours=interval_hours,
            enabled=enabled,
            tags=tags or [],
        )

        self.monitor.add_source(source)
        logger.info("Added source: %s (%s)", name, source_type)

        return source

    def remove_source(self, name: str) -> bool:
        """Remove a content source.

        Args:
            name: Source name

        Returns:
            True if removed, False if not found
        """
        removed = self.monitor.remove_source(name)
        if removed:
            logger.info("Removed source: %s", name)
        return removed
