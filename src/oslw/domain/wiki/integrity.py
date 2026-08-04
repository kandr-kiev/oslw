"""PageIntegrity - SHA256 verification and wikilink validation.

Provides:
- SHA256 body hash computation and verification
- Wikilink validation ([[slug]] → file existence)
- Broken reference detection
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger

logger = get_logger("domain.wiki.integrity")


@dataclass
class IntegrityResult:
    """Result of integrity check.

    Attributes:
        path: File path checked
        sha256_match: True if SHA256 hash matches
        sha256_expected: Expected hash (from frontmatter)
        sha256_actual: Actual hash (computed)
        broken_links: List of broken [[wikilinks]]
        missing_files: List of missing referenced files
    """

    path: Path
    sha256_match: bool = True
    sha256_expected: str = ""
    sha256_actual: str = ""
    broken_links: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)


class PageIntegrity:
    """Wiki page integrity checker.

    Provides:
    - SHA256 body hash computation
    - Wikilink extraction and validation
    - Missing file detection

    Usage:
        integrity = PageIntegrity(wiki_root="/workspace/llm-wiki")
        result = integrity.check_page("wiki/concepts/transformers.md")
        if not result.sha256_match:
            print(f"SHA256 drift: {result.sha256_expected} != {result.sha256_actual}")
    """

    # Regex for extracting [[wikilinks]]
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')

    def __init__(self, wiki_root: str | Path):
        """Initialize PageIntegrity.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.wiki_root = Path(wiki_root)

    def compute_sha256(self, file_path: str | Path) -> str:
        """Compute SHA256 hash of file body (excluding frontmatter).

        Args:
            file_path: Path to markdown file

        Returns:
            SHA256 hex digest of file body
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning("File not found: %s", path)
            return ""

        text = path.read_text(encoding="utf-8")

        # Split frontmatter (if present)
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2]  # Content after frontmatter

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def extract_sha256(self, file_path: str | Path) -> Optional[str]:
        """Extract SHA256 hash from file frontmatter.

        Args:
            file_path: Path to markdown file

        Returns:
            SHA256 hash from frontmatter, or None if not found
        """
        path = Path(file_path)
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")

        # Look for sha256 in frontmatter
        sha256_match = re.search(r'^sha256:\s*(\S+)', text, re.MULTILINE)
        if sha256_match:
            return sha256_match.group(1)

        return None

    def extract_wikilinks(self, file_path: str | Path) -> list[str]:
        """Extract all [[wikilinks]] from a file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of wikilink slugs (without [[ ]])
        """
        path = Path(file_path)
        if not path.exists():
            return []

        text = path.read_text(encoding="utf-8")
        return self.WIKILINK_PATTERN.findall(text)

    def resolve_wikilink(self, link: str) -> Optional[Path]:
        """Resolve a wikilink slug to a file path.

        Args:
            link: Wikilink slug (e.g., "transformers-architecture")

        Returns:
            Path to the file, or None if not found
        """
        # Try common patterns
        patterns = [
            self.wiki_root / "wiki" / "concepts" / f"{link}.md",
            self.wiki_root / "wiki" / "comparisons" / f"{link}.md",
            self.wiki_root / "wiki" / "playbooks" / f"{link}.md",
            self.wiki_root / "wiki" / "synthesis" / f"{link}.md",
            self.wiki_root / "wiki" / "entities" / f"{link}.md",
            self.wiki_root / "wiki" / "transcripts" / "chats" / f"{link}.md",
            self.wiki_root / "wiki" / f"{link}.md",
        ]

        for pattern in patterns:
            if pattern.exists():
                return pattern

        return None

    def check_page(self, file_path: str | Path) -> IntegrityResult:
        """Perform full integrity check on a page.

        Args:
            file_path: Path to markdown file

        Returns:
            IntegrityResult with check results
        """
        path = Path(file_path)
        result = IntegrityResult(path=path)

        # SHA256 check
        sha256_expected = self.extract_sha256(path)
        sha256_actual = self.compute_sha256(path)

        if sha256_expected and sha256_actual:
            result.sha256_expected = sha256_expected
            result.sha256_actual = sha256_actual
            result.sha256_match = sha256_expected == sha256_actual
        else:
            result.sha256_match = True  # No hash to compare

        # Wikilink check
        links = self.extract_wikilinks(path)
        for link in links:
            resolved = self.resolve_wikilink(link)
            if resolved is None:
                result.broken_links.append(link)
                logger.debug("Broken wikilink: %s in %s", link, path)

        return result

    def check_directory(self, dir_path: str | Path) -> list[IntegrityResult]:
        """Perform integrity check on all markdown files in a directory.

        Args:
            dir_path: Path to directory

        Returns:
            List of IntegrityResult for each file
        """
        path = Path(dir_path)
        results = []

        if not path.exists():
            logger.warning("Directory not found: %s", path)
            return results

        for md_file in path.rglob("*.md"):
            result = self.check_page(md_file)
            results.append(result)

        logger.info("Checked %d files in %s", len(results), path)
        return results

    def find_broken_links(self, dir_path: str | Path) -> list[tuple[str, list[str]]]:
        """Find all broken wikilinks in a directory.

        Args:
            dir_path: Path to directory

        Returns:
            List of (file_path, [broken_links]) tuples
        """
        path = Path(dir_path)
        broken = []

        if not path.exists():
            return broken

        for md_file in path.rglob("*.md"):
            links = self.extract_wikilinks(md_file)
            broken_links = [
                link for link in links
                if self.resolve_wikilink(link) is None
            ]
            if broken_links:
                broken.append((str(md_file.relative_to(self.wiki_root)), broken_links))

        return broken

    def fix_sha256(self, file_path: str | Path) -> bool:
        """Fix SHA256 hash in frontmatter.

        Args:
            file_path: Path to markdown file

        Returns:
            True if hash was updated, False if no change needed
        """
        path = Path(file_path)
        if not path.exists():
            return False

        text = path.read_text(encoding="utf-8")
        new_hash = self.compute_sha256(path)

        # Check if frontmatter exists
        if not text.startswith("---"):
            logger.warning("No frontmatter in %s, cannot fix SHA256", path)
            return False

        parts = text.split("---", 2)
        if len(parts) < 3:
            return False

        frontmatter = parts[1]
        content = parts[2]

        # Update or add sha256
        sha256_pattern = re.compile(r'^sha256:\s*\S+', re.MULTILINE)
        if sha256_pattern.search(frontmatter):
            frontmatter = sha256_pattern.sub(f"sha256: {new_hash}", frontmatter)
        else:
            # Add sha256 after title
            title_pattern = re.compile(r'^(title:\s*.+)', re.MULTILINE)
            if title_pattern.search(frontmatter):
                frontmatter = title_pattern.sub(
                    rf"\1\nsha256: {new_hash}",
                    frontmatter,
                    count=1,
                )
            else:
                frontmatter = f"sha256: {new_hash}\n{frontmatter}"

        new_text = f"---\n{frontmatter}\n---\n{content}"
        path.write_text(new_text, encoding="utf-8")
        logger.info("Fixed SHA256 in %s", path)
        return True

    def fix_wikilinks(self, file_path: str | Path) -> int:
        """Fix broken wikilinks by converting to proper slug format.

        Args:
            file_path: Path to markdown file

        Returns:
            Number of links fixed
        """
        path = Path(file_path)
        if not path.exists():
            return 0

        text = path.read_text(encoding="utf-8")
        fixed = 0

        # Replace [[Page Title]] with [[page-title]]
        def replace_link(match):
            nonlocal fixed
            link = match.group(1)

            # Already a valid slug?
            if re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', link):
                return match.group(0)

            # Convert "Page Title" to "page-title"
            slug = link.lower().replace(" ", "-")
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            slug = re.sub(r'-+', '-', slug)
            slug = slug.strip("-")

            if slug and self.resolve_wikilink(slug):
                fixed += 1
                return f"[[{slug}]]"

            return match.group(0)

        new_text = self.WIKILINK_PATTERN.sub(replace_link, text)

        if fixed > 0:
            path.write_text(new_text, encoding="utf-8")
            logger.info("Fixed %d wikilinks in %s", fixed, path)

        return fixed
