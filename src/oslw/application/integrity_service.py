"""IntegrityService — business logic for wiki integrity verification.

Orchestrates PageIntegrity and FileManager to provide
complete integrity checking and validation.

Usage:
    from oslw.config import settings
    from oslw.application import IntegrityService

    service = IntegrityService(wiki_root=settings.wiki_root)
    result = service.check_page("transformers-architecture")
    report = service.check_all_pages()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.wiki.integrity import PageIntegrity, IntegrityResult
from oslw.infrastructure.database import FileManager

logger = get_logger("application.integrity_service")


@dataclass
class IntegrityReport:
    """Report of integrity checks across all pages.

    Attributes:
        total_checked: Total pages checked
        sha256_matches: Pages with matching SHA256
        broken_links: Pages with broken wikilinks
        missing_files: Pages with missing files
        issues: List of all issues found
    """

    total_checked: int = 0
    sha256_matches: int = 0
    broken_links: int = 0
    missing_files: int = 0
    issues: list[str] = field(default_factory=list)

    @property
    def health_score(self) -> float:
        """Calculate health score (0.0 to 1.0)."""
        if self.total_checked == 0:
            return 1.0

        healthy = self.sha256_matches
        return healthy / self.total_checked


class IntegrityService:
    """Wiki integrity checking service.

    Provides:
    - Check single page integrity (SHA256, wikilinks)
    - Check all pages and generate report
    - Fix broken wikilinks
    - Verify file consistency

    Usage:
        service = IntegrityService(wiki_root=Path("./wiki"))
        result = service.check_page("transformers")
        report = service.check_all_pages()
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize IntegrityService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.integrity = PageIntegrity(wiki_root=Path(wiki_root))

    def check_page(self, slug: str) -> IntegrityResult:
        """Check integrity of a single page.

        Args:
            slug: Page slug to check

        Returns:
            IntegrityResult with check results
        """
        result = self.integrity.check_page(slug)
        logger.info("Перевірено сторінку %s: sha256=%s, посилання=%s",
                   slug, result.sha256_match, len(result.broken_links))
        return result

    def check_all_pages(self) -> IntegrityReport:
        """Check integrity of all wiki pages.

        Returns:
            IntegrityReport with comprehensive results
        """
        pages = self.file_manager.list_wiki_pages()
        report = IntegrityReport(total_checked=len(pages))

        for page_meta in pages:
            result = self.integrity.check_page(page_meta.slug)

            if result.sha256_match:
                report.sha256_matches += 1
            if result.broken_links:
                report.broken_links += 1
                for link in result.broken_links:
                    report.issues.append(
                        f"Broken link in {page_meta.slug}: {link}"
                    )
            if not result.file_exists:
                report.missing_files += 1
                report.issues.append(f"Missing file: {page_meta.slug}")

        logger.info("Перевірка цілісності: %d сторінок, рейтинг=%.2f",
                   report.total_checked, report.health_score)
        return report

    def fix_broken_links(self, slug: str) -> int:
        """Fix broken wikilinks in a page.

        Args:
            slug: Page slug to fix

        Returns:
            Number of links fixed
        """
        page = self.file_manager.read_page(slug)
        if not page:
            logger.warning("Сторінку не знайдено: %s", slug)
            return 0

        fixed = self.integrity.fix_wikilinks(page.path)
        logger.info("Виправлено %d посилань у %s", fixed, slug)
        return fixed

    def verify_all_sha256(self) -> IntegrityReport:
        """Verify SHA256 hashes for all pages.

        Returns:
            IntegrityReport with SHA256 verification results
        """
        pages = self.file_manager.list_wiki_pages()
        report = IntegrityReport(total_checked=len(pages))

        for page_meta in pages:
            result = self.integrity.check_page(page_meta.slug)
            if result.sha256_match:
                report.sha256_matches += 1
            else:
                report.issues.append(
                    f"SHA256 mismatch: {page_meta.slug}"
                )

        return report
