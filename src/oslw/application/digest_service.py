"""DigestService — business logic for newspaper digest generation.

Orchestrates NewspaperDigest and FileManager to provide
complete digest generation and management.

Usage:
    from oslw.config import settings
    from oslw.application import DigestService

    service = DigestService(wiki_root=settings.wiki_root)
    entries = service.generate_digest(hours=24)
    service.export_digest(format="markdown")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.domain.digest.newspaper import NewspaperDigest, DigestEntry
from oslw.infrastructure.database import FileManager

logger = get_logger("application.digest_service")


@dataclass
class DigestSummary:
    """Summary of a generated digest.

    Attributes:
        generated_at: Timestamp when digest was generated
        hours_covered: Number of hours covered
        total_entries: Total number of entries
        by_type: Count of entries by type
        by_source: Count of entries by source
    """

    generated_at: str = ""
    hours_covered: int = 24
    total_entries: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_source: dict[str, int] = field(default_factory=dict)


class DigestService:
    """Newspaper digest generation service.

    Provides:
    - Generate daily/hourly digests
    - Filter entries by type, source, tags
    - Export digests in various formats
    - Digest statistics and history

    Usage:
        service = DigestService(wiki_root=Path("./wiki"))
        entries = service.generate_digest(hours=24)
        summary = service.get_digest_summary(hours=24)
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize DigestService.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.file_manager = FileManager(wiki_root=Path(wiki_root))
        self.digest = NewspaperDigest(wiki_root=Path(wiki_root))

    def generate_digest(self, hours: int = 24) -> list[DigestEntry]:
        """Generate a newspaper digest for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of DigestEntry objects
        """
        entries = self.digest.generate(hours=hours)
        logger.info("Generated digest for %d hours: %d entries",
                   hours, len(entries))
        return entries

    def get_digest_summary(self, hours: int = 24) -> DigestSummary:
        """Get a summary of the digest.

        Args:
            hours: Number of hours to look back

        Returns:
            DigestSummary with statistics
        """
        entries = self.generate_digest(hours=hours)

        # Count by type
        by_type: dict[str, int] = {}
        for entry in entries:
            by_type[entry.type] = by_type.get(entry.type, 0) + 1

        # Count by source
        by_source: dict[str, int] = {}
        for entry in entries:
            source = entry.source or "unknown"
            by_source[source] = by_source.get(source, 0) + 1

        return DigestSummary(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            hours_covered=hours,
            total_entries=len(entries),
            by_type=by_type,
            by_source=by_source,
        )

    def export_digest(self, hours: int = 24,
                          format: str = "markdown") -> str:
        """Export digest in specified format.

        Args:
            hours: Number of hours to look back
            format: Output format ("markdown", "json", "text")

        Returns:
            Digest content in specified format
        """
        entries = self.generate_digest(hours=hours)

        if format == "markdown":
            return self._export_markdown(entries)
        elif format == "json":
            import json
            return json.dumps(
                [e.to_dict() for e in entries],
                indent=2,
                ensure_ascii=False,
            )
        elif format == "text":
            return self._export_text(entries)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(self, entries: list[DigestEntry]) -> str:
        """Export digest as Markdown."""
        lines = [
            "# LLM-Wiki Daily Digest",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        # Group by type
        by_type: dict[str, list[DigestEntry]] = {}
        for entry in entries:
            if entry.type not in by_type:
                by_type[entry.type] = []
            by_type[entry.type].append(entry)

        for entry_type, type_entries in sorted(by_type.items()):
            lines.append(f"## {entry_type.title()}")
            lines.append("")

            for entry in type_entries:
                lines.append(f"### {entry.page}")
                lines.append(f"- **Source:** {entry.source or 'N/A'}")
                lines.append(f"- **Time:** {entry.timestamp}")
                if entry.description:
                    lines.append(f"- **Description:** {entry.description}")
                lines.append("")

        return "\n".join(lines)

    def _export_text(self, entries: list[DigestEntry]) -> str:
        """Export digest as plain text."""
        lines = []
        for entry in entries:
            lines.append(
                f"[{entry.type}] {entry.page} "
                f"({entry.source or 'N/A'}) - {entry.timestamp}"
            )
            if entry.description:
                lines.append(f"  {entry.description}")
            lines.append("")

        return "\n".join(lines)

    def get_recent_entries(self, limit: int = 10,
                               hours: int = 24) -> list[DigestEntry]:
        """Get most recent digest entries.

        Args:
            limit: Maximum number of entries
            hours: Number of hours to look back

        Returns:
            List of recent DigestEntry objects
        """
        entries = self.generate_digest(hours=hours)
        return entries[:limit]
