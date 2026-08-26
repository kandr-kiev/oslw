"""WikiDoctor - diagnose and fix wiki issues.

Provides:
- Multi-layer diagnostic (index, wiki_pages, metadata)
- Automated fixes (cure)
- Report generation
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.core.exceptions import DoctorError

logger = get_logger("domain.quality.doctor")


@dataclass
class DiagnosisIssue:
    """Single issue found during diagnosis.

    Attributes:
        layer: Layer where issue was found (index, wiki_pages, metadata)
        severity: Issue severity (critical, warning, info)
        code: Issue code (e.g., "MISSING_SLUG", "BROKEN_LINK")
        file: File path where issue was found
        description: Human-readable description
        suggestion: Suggested fix
    """

    layer: str
    severity: str
    code: str
    file: str
    description: str
    suggestion: str = ""


@dataclass
class DiagnosisResult:
    """Result of a wiki diagnosis.

    Attributes:
        timestamp: When diagnosis was run
        wiki_root: Wiki root path
        total_pages: Total wiki pages checked
        issues: List of issues found
        summary: Summary statistics
    """

    timestamp: datetime = field(default_factory=datetime.now)
    wiki_root: str = ""
    total_pages: int = 0
    issues: list[DiagnosisIssue] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


class WikiDoctor:
    """WikiDoctor - diagnose and fix wiki issues.

    Provides multi-layer diagnosis:
    1. index: Check index.md consistency
    2. wiki_pages: Check wiki page structure
    3. metadata: Check frontmatter fields

    Usage:
        doctor = WikiDoctor(wiki_root=Path("./wiki"))
        result = doctor.diagnose(layer="all")
        for issue in result.issues:
            print(f"[{issue.severity}] {issue.code}: {issue.file}")
    """

    # Required frontmatter fields
    REQUIRED_FIELDS = {"title", "slug", "type", "tags", "created", "updated"}
    VALID_TYPES = {"concept", "comparison", "playbook", "synthesis", "entity", "event"}

    def __init__(self, wiki_root: str | Path):
        """Initialize WikiDoctor.

        Args:
            wiki_root: Path to wiki root directory (configurable, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)

    def diagnose(self, layer: str = "all") -> DiagnosisResult:
        """Run wiki diagnosis.

        Args:
            layer: Layer to check ("index", "wiki_pages", "metadata", "all")

        Returns:
            DiagnosisResult with issues found
        """
        result = DiagnosisResult(wiki_root=str(self.wiki_root))
        issues = []

        if layer in ("index", "all"):
            issues.extend(self._check_index())

        if layer in ("wiki_pages", "all"):
            issues.extend(self._check_wiki_pages(result))

        if layer in ("metadata", "all"):
            issues.extend(self._check_metadata())

        result.issues = issues
        result.total_pages = sum(1 for _ in self.wiki_root.glob("**/*.md"))

        # Generate summary
        result.summary = {
            "total_issues": len(issues),
            "critical": sum(1 for i in issues if i.severity == "critical"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
            "by_layer": {
                "index": sum(1 for i in issues if i.layer == "index"),
                "wiki_pages": sum(1 for i in issues if i.layer == "wiki_pages"),
                "metadata": sum(1 for i in issues if i.layer == "metadata"),
            },
        }

        logger.info(
            "Diagnosis complete: %d issues (%d critical, %d warning, %d info)",
            len(issues),
            result.summary["critical"],
            result.summary["warning"],
            result.summary["info"],
        )

        return result

    # Directories excluded from quality checks (service/infra, not knowledge content)
    EXCLUDED_DIRS = {".git", ".obsidian", ".hermes", "_archive", "logs", "config",
                     "docs", "templates", "raw", "node_modules", "__pycache__"}
    EXCLUDED_FILES = {"index.md", "SCHEMA.md", "log.md", "README.md", "CHANGELOG.md"}

    def _is_content_page(self, md_file) -> bool:
        """True if the file is a Layer 2 wiki content page."""
        if md_file.name in self.EXCLUDED_FILES:
            return False
        rel_parts = set(md_file.relative_to(self.wiki_root).parts[:-1])
        return not (rel_parts & self.EXCLUDED_DIRS)

    def _check_index(self) -> list[DiagnosisIssue]:
        """Check index.md consistency.

        Returns:
            List of issues found
        """
        issues = []
        index_path = self.wiki_root / "index.md"

        if not index_path.exists():
            issues.append(DiagnosisIssue(
                layer="index",
                severity="critical",
                code="INDEX_MISSING",
                file=str(index_path),
                description="Index file missing",
                suggestion="Run 'oslw sync' to regenerate index",
            ))
            return issues

        # Parse index entries
        text = index_path.read_text(encoding="utf-8")
        index_slugs = set()
        for line in text.splitlines():
            match = re.match(r'^###\s+(\S+)\s+\[([^\]]+)\]', line)
            if match:
                index_slugs.add(match.group(1))

        # Check for orphaned wiki files (not in index)
        wiki_dir = self.wiki_root
        for md_file in wiki_dir.rglob("*.md"):
            if not self._is_content_page(md_file):
                continue
            slug = md_file.stem
            if slug not in index_slugs:
                issues.append(DiagnosisIssue(
                    layer="index",
                    severity="warning",
                    code="ORPHANED_PAGE",
                    file=str(md_file.relative_to(self.wiki_root)),
                    description=f"Page '{slug}' not in index.md",
                    suggestion="Add entry to index.md or remove file",
                ))

        return issues

    def _check_wiki_pages(self, result: DiagnosisResult) -> list[DiagnosisIssue]:
        """Check wiki page structure.

        Args:
            result: DiagnosisResult to update

        Returns:
            List of issues found
        """
        issues = []
        wiki_dir = self.wiki_root

        for md_file in wiki_dir.rglob("*.md"):
            if not self._is_content_page(md_file):
                continue

            text = md_file.read_text(encoding="utf-8")

            # Check for required sections
            if "## " not in text and len(text) > 200:
                issues.append(DiagnosisIssue(
                    layer="wiki_pages",
                    severity="info",
                    code="NO_SECTIONS",
                    file=str(md_file.relative_to(self.wiki_root)),
                    description="Page has no section headers",
                    suggestion="Add section headers for better structure",
                ))

            # Check for broken wikilinks
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', text)
            for link in links:
                if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', link):
                    continue  # Skip non-slugs

                # Check if linked file exists
                patterns = [
                    wiki_dir / "concept" / f"{link}.md",
                    wiki_dir / "comparisons" / f"{link}.md",
                    wiki_dir / "playbooks" / f"{link}.md",
                    wiki_dir / "synthesis" / f"{link}.md",
                    wiki_dir / f"{link}.md",
                ]
                if not any(p.exists() for p in patterns):
                    issues.append(DiagnosisIssue(
                        layer="wiki_pages",
                        severity="warning",
                        code="BROKEN_LINK",
                        file=str(md_file.relative_to(self.wiki_root)),
                        description=f"Broken wikilink: [[{link}]]",
                        suggestion=f"Create page '{link}.md' or remove link",
                    ))

        return issues

    def _check_metadata(self) -> list[DiagnosisIssue]:
        """Check frontmatter metadata.

        Returns:
            List of issues found
        """
        issues = []
        wiki_dir = self.wiki_root

        for md_file in wiki_dir.rglob("*.md"):
            if not self._is_content_page(md_file):
                continue

            text = md_file.read_text(encoding="utf-8")

            # Check for frontmatter
            if not text.startswith("---"):
                issues.append(DiagnosisIssue(
                    layer="metadata",
                    severity="critical",
                    code="MISSING_FRONTMATTER",
                    file=str(md_file.relative_to(self.wiki_root)),
                    description="Page missing frontmatter",
                    suggestion="Add YAML frontmatter with required fields",
                ))
                continue

            # Extract frontmatter
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue

            frontmatter = parts[1]

            # Check required fields
            for field_name in self.REQUIRED_FIELDS:
                if not re.search(rf'^{field_name}:\s*', frontmatter, re.MULTILINE):
                    issues.append(DiagnosisIssue(
                        layer="metadata",
                        severity="warning",
                        code=f"MISSING_FIELD_{field_name.upper()}",
                        file=str(md_file.relative_to(self.wiki_root)),
                        description=f"Missing required field: {field_name}",
                        suggestion=f"Add '{field_name}' to frontmatter",
                    ))

            # Validate type
            type_match = re.search(r'^type:\s*(\S+)', frontmatter, re.MULTILINE)
            if type_match and type_match.group(1) not in self.VALID_TYPES:
                issues.append(DiagnosisIssue(
                    layer="metadata",
                    severity="warning",
                    code="INVALID_TYPE",
                    file=str(md_file.relative_to(self.wiki_root)),
                    description=f"Invalid page type: {type_match.group(1)}",
                    suggestion=f"Use one of: {', '.join(self.VALID_TYPES)}",
                ))

        return issues

    def cure(self, layer: str = "all", dry_run: bool = True) -> DiagnosisResult:
        """Run automated fixes.

        Args:
            layer: Layer to fix ("index", "wiki_pages", "metadata", "all")
            dry_run: If True, don't apply fixes

        Returns:
            DiagnosisResult with issues after fixing
        """
        logger.info("Запуск лікування WikiDoctor (layer=%s, dry_run=%s)", layer, dry_run)

        # Run diagnosis first
        result = self.diagnose(layer)

        # Apply fixes
        if layer in ("index", "all"):
            self._fix_index(dry_run=dry_run)

        if layer in ("metadata", "all"):
            self._fix_metadata(dry_run=dry_run)

        # Re-diagnose after fixes
        result = self.diagnose(layer)

        logger.info("Лікування завершено: залишилось %d проблем", len(result.issues))
        return result

    def _fix_index(self, dry_run: bool = True) -> None:
        """Fix index.md by adding orphaned pages.

        Args:
            dry_run: If True, don't apply changes
        """
        index_path = self.wiki_root / "index.md"
        wiki_dir = self.wiki_root

        # Parse existing index
        existing_slugs = set()
        if index_path.exists():
            text = index_path.read_text(encoding="utf-8")
            for line in text.splitlines():
                match = re.match(r'^###\s+(\S+)\s+\[([^\]]+)\]', line)
                if match:
                    existing_slugs.add(match.group(1))

        # Find orphaned pages
        orphaned = []
        for md_file in wiki_dir.rglob("*.md"):
            if not self._is_content_page(md_file):
                continue
            slug = md_file.stem
            if slug not in existing_slugs:
                orphaned.append((slug, str(md_file.relative_to(wiki_dir))))

        if orphaned:
            logger.info("Знайдено %d сирітських сторінок для додавання в індекс", len(orphaned))
            if not dry_run:
                # Add entries to index
                text = index_path.read_text(encoding="utf-8")
                for slug, path in orphaned:
                    entry = f"\n### {slug} [{path}]"
                    text += entry
                index_path.write_text(text, encoding="utf-8")

    def _fix_metadata(self, dry_run: bool = True) -> None:
        """Fix missing metadata fields.

        Args:
            dry_run: If True, don't apply changes
        """
        wiki_dir = self.wiki_root

        for md_file in wiki_dir.rglob("*.md"):
            if not self._is_content_page(md_file):
                continue

            text = md_file.read_text(encoding="utf-8")

            # Skip if no frontmatter
            if not text.startswith("---"):
                if not dry_run:
                    # Add default frontmatter
                    slug = md_file.stem
                    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    frontmatter = (
                        f"---\n"
                        f"title: {slug.replace('-', ' ').title()}\n"
                        f"slug: {slug}\n"
                        f"type: concept\n"
                        f"tags: []\n"
                        f"created: {now}\n"
                        f"updated: {now}\n"
                        f"---\n"
                    )
                    text = frontmatter + text
                    md_file.write_text(text, encoding="utf-8")
                    logger.info("Додано стандартний frontmatter до %s", md_file)
