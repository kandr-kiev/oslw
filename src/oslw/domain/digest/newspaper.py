"""NewspaperDigest - daily newspaper-style digest generation.

Generates daily digests from wiki changes:
- New pages added
- Pages updated
- Sources monitored
- Graph statistics
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger

logger = get_logger("domain.digest.newspaper")


@dataclass
class DigestEntry:
    """Single entry in the daily digest.

    Attributes:
        timestamp: When the change occurred
        type: Change type (new, updated, deleted)
        page: Page slug
        title: Page title
        description: Brief description of change
    """

    timestamp: datetime
    type: str
    page: str
    title: str
    description: str = ""


class NewspaperDigest:
    """Daily newspaper-style digest generator.

    Generates daily digests from wiki changes:
    - New pages added
    - Pages updated
    - Sources monitored
    - Graph statistics

    Usage:
        digest = NewspaperDigest(wiki_root="/workspace/llm-wiki")
        entries = digest.generate(hours=24)
        for entry in entries:
            print(f"[{entry.type}] {entry.page}: {entry.title}")
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize NewspaperDigest.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.wiki_root = Path(wiki_root)

    def generate(self, hours: int = 24) -> list[DigestEntry]:
        """Generate digest for the past N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of DigestEntry sorted by timestamp
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        entries = []

        # Check wiki pages for recent changes
        entries.extend(self._check_recent_changes(cutoff))

        # Check sources for recent activity
        entries.extend(self._check_sources())

        # Sort by timestamp
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        logger.info("Generated digest with %d entries", len(entries))
        return entries

    def _check_recent_changes(self, cutoff: datetime) -> list[DigestEntry]:
        """Check wiki pages for recent changes.

        Args:
            cutoff: Cutoff timestamp

        Returns:
            List of DigestEntry
        """
        entries = []
        wiki_dir = self.wiki_root / "wiki"

        if not wiki_dir.exists():
            return entries

        for md_file in wiki_dir.rglob("*.md"):
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue

            # Check file modification time
            mtime = datetime.fromtimestamp(
                md_file.stat().st_mtime, tz=timezone.utc
            )

            if mtime >= cutoff:
                # Extract title from frontmatter
                text = md_file.read_text(encoding="utf-8")
                title = self._extract_title(text) or md_file.stem

                entries.append(DigestEntry(
                    timestamp=mtime,
                    type="updated",
                    page=md_file.stem,
                    title=title,
                    description=f"Page updated at {mtime.strftime('%Y-%m-%d %H:%M')}",
                ))

        return entries

    def _check_sources(self) -> list[DigestEntry]:
        """Check sources for recent activity.

        Returns:
            List of DigestEntry
        """
        entries = []
        raw_dir = self.wiki_root / "raw"

        if not raw_dir.exists():
            return entries

        # Check for new raw articles
        for md_file in raw_dir.rglob("*.md"):
            # Check if file is recent (new articles)
            mtime = datetime.fromtimestamp(
                md_file.stat().st_mtime, tz=timezone.utc
            )

            if mtime >= datetime.now(timezone.utc) - timedelta(hours=24):
                text = md_file.read_text(encoding="utf-8")
                title = self._extract_title(text) or md_file.stem

                entries.append(DigestEntry(
                    timestamp=mtime,
                    type="new",
                    page=md_file.stem,
                    title=title,
                    description=f"New raw article from source",
                ))

        return entries

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from frontmatter.

        Args:
            text: File content

        Returns:
            Title or None
        """
        match = re.search(r'^title:\s*(.+)', text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def format_as_markdown(self, entries: list[DigestEntry]) -> str:
        """Format digest entries as markdown.

        Args:
            entries: List of DigestEntry

        Returns:
            Markdown-formatted digest
        """
        lines = [
            "# 📰 Daily Digest",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        # Group by type
        new_entries = [e for e in entries if e.type == "new"]
        updated_entries = [e for e in entries if e.type == "updated"]

        if new_entries:
            lines.append("## 🆕 New Pages")
            for entry in new_entries:
                lines.append(f"- **{entry.title}** (`{entry.page}`)")
                if entry.description:
                    lines.append(f"  - {entry.description}")
            lines.append("")

        if updated_entries:
            lines.append("## ✏️ Updated Pages")
            for entry in updated_entries:
                lines.append(f"- **{entry.title}** (`{entry.page}`)")
                if entry.description:
                    lines.append(f"  - {entry.description}")
            lines.append("")

        if not new_entries and not updated_entries:
            lines.append("No changes in the last 24 hours.")

        return "\n".join(lines)
