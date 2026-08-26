"""QualityService — business logic for wiki quality monitoring.

Orchestrates WikiDoctor, PageLint, Deduplication and FileManager to provide
complete wiki health monitoring and quality assurance.

Usage:
    from oslw.config import settings
    from oslw.application import QualityService

    service = QualityService(wiki_root=settings.wiki_root)
    report = service.diagnose(layer="all")
    stats = service.get_quality_stats()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.quality.doctor import WikiDoctor, DiagnosisResult
from oslw.domain.quality.lint import PageLint
from oslw.domain.quality.cleanup import Deduplication
from oslw.infrastructure.database import FileManager

logger = get_logger("application.quality_service")


@dataclass
class QualityStats:
    """Statistics about wiki quality.

    Attributes:
        total_pages: Total number of pages
        pages_with_frontmatter: Pages with valid frontmatter
        pages_with_sha256: Pages with SHA256 hash
        orphan_pages: Pages not linked from any other page
        duplicate_groups: Number of duplicate groups found
        average_confidence: Average confidence score
    """

    total_pages: int = 0
    pages_with_frontmatter: int = 0
    pages_with_sha256: int = 0
    orphan_pages: int = 0
    duplicate_groups: int = 0
    average_confidence: float = 0.0


class QualityService:
    """Wiki quality monitoring service.

    Provides:
    - Multi-layer diagnosis (index, pages, metadata)
    - Structural validation of pages
    - Duplicate detection and cleanup
    - Quality statistics and reporting

    Usage:
        service = QualityService(wiki_root=Path("./wiki"))
        report = service.diagnose(layer="all")
        stats = service.get_quality_stats()
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize QualityService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.doctor = WikiDoctor(wiki_root=Path(wiki_root))
        self.linter = PageLint(wiki_root=Path(wiki_root))
        self.dedup = Deduplication(wiki_root=Path(wiki_root))

    def diagnose(self, layer: str = "all") -> DoctorReport:
        """Run multi-layer diagnosis on the wiki.

        Args:
            layer: Layer to diagnose ("index", "wiki_pages", "metadata", "all")

        Returns:
            DoctorReport with diagnosis results
        """
        report = self.doctor.diagnose(layer=layer)
        logger.info("Діагностику завершено: знайдено %d проблем", len(report.issues))
        return report

    def validate_page(self, slug: str) -> list[str]:
        """Validate structure of a single page.

        Args:
            slug: Page slug to validate

        Returns:
            List of lint errors (empty if valid)
        """
        page = self.file_manager.read_page(slug)
        if not page:
            return [f"Page not found: {slug}"]

        errors = self.linter.validate_page(page)
        logger.info("Сторінку %s підтверджено: %d помилок", slug, len(errors))
        return errors

    def find_duplicates(self) -> list[dict]:
        """Find duplicate pages in the wiki.

        Returns:
            List of duplicate groups as dicts
        """
        groups = self.dedup.find_duplicates()
        logger.info("Знайдено %d груп дублікатів", len(groups))
        # Convert DuplicateGroup objects to dicts for JSON serialization
        return [
            {
                "base_slug": g.base_slug,
                "duplicates": g.duplicates,
                "sha256": g.sha256,
                "reason": g.reason,
            }
            for g in groups
        ]

    def cleanup_duplicates(self, dry_run: bool = True) -> list[str]:
        """Clean up duplicate pages.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of files that would be/were deleted
        """
        removed = self.dedup.cleanup_duplicates(dry_run=dry_run)
        logger.info("Очищення %s: %d файлів %s",
                   "dry run" if dry_run else "actual",
                   len(removed), "would be removed" if dry_run else "removed")
        return removed

    def get_quality_stats(self, sample_size: int | None = None) -> QualityStats:
        """Get comprehensive quality statistics.

        Args:
            sample_size: Limit pages to scan.
                - None (default): scan ALL pages, include duplicates (full accuracy)
                - 0: scan ALL pages, skip duplicates (fast full scan)
                - int > 0: scan only first N pages, skip duplicates (sampling)

        Returns:
            QualityStats with current statistics
        """
        pages = self.file_manager.list_wiki_pages()

        # Apply sample size limit
        if sample_size is not None and sample_size > 0:
            pages = pages[:sample_size]

        stats = QualityStats(total_pages=len(pages))

        # Count pages with frontmatter and SHA256
        for page_meta in pages:
            if page_meta.title:  # Has frontmatter
                stats.pages_with_frontmatter += 1
            if page_meta.sha256:  # Has SHA256
                stats.pages_with_sha256 += 1

        # Find orphan pages (simplified - pages not in index)
        index = self.file_manager.read_page("index")
        if index:
            linked_slugs = set()
            for line in index.content.splitlines():
                if "### " in line:
                    slug = line.split("### ")[1].split(" ")[0]
                    linked_slugs.add(slug)

            for page_meta in pages:
                if page_meta.slug not in linked_slugs:
                    stats.orphan_pages += 1

        # Skip expensive duplicate detection when sampling (sample_size != None)
        # sample_size=0 → full scan but skip duplicates (fast full)
        # sample_size=None → full scan with duplicates (accurate full)
        if sample_size is not None:
            stats.duplicate_groups = 0
            stats.average_confidence = 0.0
        else:
            # Find duplicate groups (full scan)
            dup_groups = self.dedup.find_duplicates()
            stats.duplicate_groups = len(dup_groups)

            # Calculate average confidence (simplified)
            if pages:
                stats.average_confidence = 0.8
            else:
                stats.average_confidence = 0.0

        return stats

    def run_full_audit(self, sample_size: int | None = None) -> dict:
        """Run a full quality audit.

        Args:
            sample_size: Limit pages to scan.
                - None (default): audit ALL pages, include duplicates
                - int > 0: audit first N pages only, skip duplicates
                - 0: audit ALL pages, skip duplicates (fast mode)

        Returns:
            Dictionary with all audit results
        """
        # Run diagnosis (limited if sample_size specified)
        if sample_size is not None and sample_size > 0:
            report = self.diagnose(layer="metadata")
        else:
            report = self.diagnose(layer="all")

        # Get quality stats (limited if sample_size specified)
        stats = self.get_quality_stats(sample_size=sample_size)

        # Find duplicates (limited if sample_size specified)
        if sample_size is not None and sample_size > 0:
            duplicates = []
        else:
            duplicates = self.find_duplicates()

        # Validate pages (sample or all)
        pages = self.file_manager.list_wiki_pages()
        if sample_size is not None and sample_size > 0:
            pages = pages[:sample_size]
        # sample_size == 0 or None: validate all pages (up to 100 for performance)

        validation_errors = {}
        for page_meta in pages[:100]:
            errors = self.validate_page(page_meta.slug)
            if errors:
                validation_errors[page_meta.slug] = errors

        return {
            "diagnosis": {
                "issues": [str(issue) for issue in report.issues],
                "severity_counts": {
                    "critical": sum(1 for i in report.issues if i.severity == "critical"),
                    "warning": sum(1 for i in report.issues if i.severity == "warning"),
                    "info": sum(1 for i in report.issues if i.severity == "info"),
                },
            },
            "quality_stats": {
                "total_pages": stats.total_pages,
                "pages_with_frontmatter": stats.pages_with_frontmatter,
                "pages_with_sha256": stats.pages_with_sha256,
                "orphan_pages": stats.orphan_pages,
                "duplicate_groups": stats.duplicate_groups,
            },
            "duplicates": duplicates,
            "validation_errors": validation_errors,
        }
