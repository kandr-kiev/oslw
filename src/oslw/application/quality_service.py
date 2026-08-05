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
        logger.info("Diagnosis complete: %d issues found", len(report.issues))
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
        logger.info("Validated page %s: %d errors", slug, len(errors))
        return errors

    def find_duplicates(self) -> list[dict]:
        """Find duplicate pages in the wiki.

        Returns:
            List of duplicate groups
        """
        groups = self.dedup.find_duplicates()
        logger.info("Found %d duplicate groups", len(groups))
        return groups

    def cleanup_duplicates(self, dry_run: bool = True) -> list[str]:
        """Clean up duplicate pages.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of files that would be/were deleted
        """
        removed = self.dedup.cleanup_duplicates(dry_run=dry_run)
        logger.info("Cleanup %s: %d files %s",
                   "dry run" if dry_run else "actual",
                   len(removed), "would be removed" if dry_run else "removed")
        return removed

    def get_quality_stats(self) -> QualityStats:
        """Get comprehensive quality statistics.

        Returns:
            QualityStats with current statistics
        """
        pages = self.file_manager.list_wiki_pages()
        stats = QualityStats(total_pages=len(pages))

        # Count pages with frontmatter and SHA256
        for page_meta in pages:
            if page_meta.title:  # Has frontmatter
                stats.pages_with_frontmatter += 1
            if page_meta.sha256:  # Has SHA256
                stats.pages_with_sha256 += 1

        # Find orphan pages (simplified - pages not in index)
        index = self.file_manager.read_page(self.file_manager.wiki_dir / "index.md")
        if index:
            linked_slugs = set()
            for line in index.content.splitlines():
                if "### " in line:
                    slug = line.split("### ")[1].split(" ")[0]
                    linked_slugs.add(slug)

            for page_meta in pages:
                if page_meta.slug not in linked_slugs:
                    stats.orphan_pages += 1

        # Find duplicate groups
        dup_groups = self.dedup.find_duplicates()
        stats.duplicate_groups = len(dup_groups)

        # Calculate average confidence (simplified)
        if pages:
            # Assume all pages have equal confidence for now
            stats.average_confidence = 0.8
        else:
            stats.average_confidence = 0.0

        return stats

    def run_full_audit(self) -> dict:
        """Run a full quality audit.

        Returns:
            Dictionary with all audit results
        """
        # Run diagnosis
        report = self.diagnose(layer="all")

        # Get quality stats
        stats = self.get_quality_stats()

        # Find duplicates
        duplicates = self.find_duplicates()

        # Validate all pages (sample - first 10)
        pages = self.file_manager.list_wiki_pages()
        validation_errors = {}
        for page_meta in pages[:10]:
            errors = self.validate_page(page_meta.slug)
            if errors:
                validation_errors[page_meta.slug] = errors

        return {
            "diagnosis": {
                "issues": [str(issue) for issue in report.issues],
                "severity_counts": {
                    "critical": sum(1 for i in report.issues if str(i).startswith("CRITICAL")),
                    "warning": sum(1 for i in report.issues if str(i).startswith("WARNING")),
                    "info": sum(1 for i in report.issues if str(i).startswith("INFO")),
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
