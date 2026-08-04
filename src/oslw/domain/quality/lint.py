"""PageLint - structural validation for wiki pages.

Validates:
- Frontmatter completeness
- Section structure
- Content quality metrics
- Wikilink consistency
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class LintIssue:
    """Single lint issue.

    Attributes:
        severity: Issue severity (error, warning, info)
        code: Issue code
        message: Human-readable message
        line: Line number (if applicable)
    """

    severity: str
    code: str
    message: str
    line: Optional[int] = None


@dataclass
class LintResult:
    """Result of a lint check.

    Attributes:
        file: File path
        issues: List of issues found
        score: Quality score (0.0-1.0)
    """

    file: str
    issues: list[LintIssue] = field(default_factory=list)
    score: float = 1.0


class PageLint:
    """Wiki page structural linter.

    Checks:
    - Frontmatter completeness
    - Section structure (H2, H3)
    - Content length
    - Wikilink validity
    - Heading hierarchy

    Usage:
        lint = PageLint()
        result = lint.check_file("wiki/concepts/transformers.md")
        print(f"Score: {result.score}")
        for issue in result.issues:
            print(f"[{issue.severity}] {issue.code}: {issue.message}")
    """

    # Minimum content lengths
    MIN_CONTENT_LENGTH = 100  # characters
    MIN_SECTION_LENGTH = 50   # characters per section
    MIN_HEADINGS_PER_PAGE = 2 # at least 2 H2 headings

    # Required section patterns
    REQUIRED_SECTIONS = ["description", "overview"]

    def check_file(self, file_path: str | Path) -> LintResult:
        """Lint a single wiki page.

        Args:
            file_path: Path to markdown file

        Returns:
            LintResult with issues and score
        """
        path = Path(file_path)
        result = LintResult(file=str(path))

        if not path.exists():
            result.issues.append(LintIssue(
                severity="error",
                code="FILE_NOT_FOUND",
                message=f"File not found: {path}",
            ))
            result.score = 0.0
            return result

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Run all checks
        self._check_frontmatter(text, result)
        self._check_headings(lines, result)
        self._check_content_length(text, result)
        self._check_wikilinks(text, result)
        self._check_heading_hierarchy(lines, result)

        # Calculate score
        result.score = self._calculate_score(result)

        return result

    def check_directory(self, dir_path: str | Path) -> list[LintResult]:
        """Lint all markdown files in a directory.

        Args:
            dir_path: Path to directory

        Returns:
            List of LintResult for each file
        """
        path = Path(dir_path)
        results = []

        for md_file in path.rglob("*.md"):
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue
            result = self.check_file(md_file)
            results.append(result)

        return results

    def _check_frontmatter(self, text: str, result: LintResult) -> None:
        """Check frontmatter completeness.

        Args:
            text: File content
            result: LintResult to update
        """
        required_fields = {"title", "slug", "type", "tags", "created", "updated"}

        if not text.startswith("---"):
            result.issues.append(LintIssue(
                severity="error",
                code="NO_FRONTMATTER",
                message="Missing YAML frontmatter",
            ))
            return

        parts = text.split("---", 2)
        if len(parts) < 3:
            result.issues.append(LintIssue(
                severity="error",
                code="INVALID_FRONTMATTER",
                message="Malformed YAML frontmatter",
            ))
            return

        frontmatter = parts[1]

        for field_name in required_fields:
            if not re.search(rf'^{field_name}:\s*', frontmatter, re.MULTILINE):
                result.issues.append(LintIssue(
                    severity="warning",
                    code=f"MISSING_FIELD_{field_name.upper()}",
                    message=f"Missing required field: {field_name}",
                ))

    def _check_headings(self, lines: list[str], result: LintResult) -> None:
        """Check heading structure.

        Args:
            lines: File lines
            result: LintResult to update
        """
        h2_count = sum(1 for line in lines if re.match(r'^##\s+', line))
        h3_count = sum(1 for line in lines if re.match(r'^###\s+', line))

        if h2_count < self.MIN_HEADINGS_PER_PAGE:
            result.issues.append(LintIssue(
                severity="warning",
                code="LOW_HEADINGS",
                message=f"Only {h2_count} H2 headings (recommended: {self.MIN_HEADINGS_PER_PAGE}+)",
            ))

    def _check_content_length(self, text: str, result: LintResult) -> None:
        """Check content length.

        Args:
            text: File content
            result: LintResult to update
        """
        # Strip frontmatter
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2]

        content_length = len(text.strip())

        if content_length < self.MIN_CONTENT_LENGTH:
            result.issues.append(LintIssue(
                severity="warning",
                code="SHORT_CONTENT",
                message=f"Content too short: {content_length} chars (min: {self.MIN_CONTENT_LENGTH})",
            ))

    def _check_wikilinks(self, text: str, result: LintResult) -> None:
        """Check wikilink validity.

        Args:
            text: File content
            result: LintResult to update
        """
        import re
        links = re.findall(r'\[\[([^\]]+)\]\]', text)
        invalid = []

        for link in links:
            # Skip non-slugs
            if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', link):
                continue
            invalid.append(link)

        if invalid:
            result.issues.append(LintIssue(
                severity="info",
                code="WIKILINKS_FOUND",
                message=f"Found {len(invalid)} wikilinks (validation requires file system)",
            ))

    def _check_heading_hierarchy(self, lines: list[str], result: LintResult) -> None:
        """Check heading hierarchy (no skipping levels).

        Args:
            lines: File lines
            result: LintResult to update
        """
        max_level = 0
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+', line)
            if match:
                level = len(match.group(1))
                if level > max_level + 1 and max_level > 0:
                    result.issues.append(LintIssue(
                        severity="warning",
                        code="HEADING_SKIP",
                        message=f"Heading level jump: H{max_level} -> H{level}",
                        line=i + 1,
                    ))
                max_level = level

    def _calculate_score(self, result: LintResult) -> float:
        """Calculate quality score.

        Args:
            result: LintResult to score

        Returns:
            Score between 0.0 and 1.0
        """
        if not result.issues:
            return 1.0

        # Deduct points per issue
        penalties = {
            "error": 0.3,
            "warning": 0.1,
            "info": 0.0,
        }

        total_penalty = sum(
            penalties.get(issue.severity, 0.0)
            for issue in result.issues
        )

        return max(0.0, 1.0 - total_penalty)
