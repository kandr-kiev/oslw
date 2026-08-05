"""SourceConfig - configuration for source monitors.

Defines source types, URLs, and monitoring parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class SourceType(str, Enum):
    """Types of content sources."""

    RSS = "rss"
    GITHUB = "github"
    HUGGINGFACE = "huggingface"
    YOUTUBE = "youtube"
    LOCAL = "local"


@dataclass
class SourceConfig:
    """Configuration for a single source monitor.

    Attributes:
        name: Unique source name (e.g., "hacker-news", "kandr-kiev/llm-wiki")
        type: Source type (rss, github, huggingface, youtube, local)
        url: Source URL
        enabled: Whether monitoring is active
        interval_hours: Check interval in hours
        last_checked: Last successful check timestamp
        last_error: Last error message (if any)
        articles_count: Total articles collected from this source
        tags: Default tags for articles from this source
    """

    name: str
    type: SourceType
    url: str
    enabled: bool = True
    interval_hours: int = 6
    last_checked: Optional[datetime] = None
    last_error: Optional[str] = None
    articles_count: int = 0
    tags: list[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Check if source is active and due for check."""
        if not self.enabled:
            return False

        if self.last_checked is None:
            return True

        elapsed = (datetime.now(timezone.utc) - self.last_checked).total_seconds()
        return elapsed >= self.interval_hours * 3600

    def record_check(self, success: bool, error: Optional[str] = None) -> None:
        """Record a check result.

        Args:
            success: Whether the check was successful
            error: Error message if check failed
        """
        self.last_checked = datetime.now(timezone.utc)
        if success:
            self.last_error = None
        else:
            self.last_error = error

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "url": self.url,
            "enabled": self.enabled,
            "interval_hours": self.interval_hours,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_error": self.last_error,
            "articles_count": self.articles_count,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SourceConfig:
        """Create from dictionary."""
        type_val = data.get("type", "rss")
        if isinstance(type_val, str):
            try:
                type_val = SourceType(type_val)
            except ValueError:
                type_val = SourceType.RSS

        last_checked = data.get("last_checked")
        if isinstance(last_checked, str):
            try:
                last_checked = datetime.fromisoformat(last_checked)
            except (ValueError, TypeError):
                last_checked = None

        return cls(
            name=data["name"],
            type=type_val,
            url=data["url"],
            enabled=data.get("enabled", True),
            interval_hours=data.get("interval_hours", 6),
            last_checked=last_checked,
            last_error=data.get("last_error"),
            articles_count=data.get("articles_count", 0),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:
        return f"SourceConfig(name='{self.name}', type={self.type.value})"


class SourceMonitor:
    """Monitor configuration and management for content sources.

    Provides:
    - List configured sources
    - Monitor sources for updates
    - Add/remove sources
    - Source configuration persistence

    Usage:
        monitor = SourceMonitor(wiki_root=Path("./wiki"))
        sources = monitor.list_sources()
        results = monitor.monitor_all()
        monitor.add_source(SourceConfig(...))
    """

    SOURCES_FILE = "sources.json"

    def __init__(self, wiki_root: str | Path):
        """Initialize SourceMonitor.

        Args:
            wiki_root: Path to wiki root directory
        """
        self.wiki_root = Path(wiki_root)
        self.sources_file = self.wiki_root / "config" / self.SOURCES_FILE
        self._sources: dict[str, SourceConfig] = {}
        self._load_sources()

    def _load_sources(self) -> None:
        """Load sources from JSON file."""
        import json
        if not self.sources_file.exists():
            return
        try:
            data = json.loads(self.sources_file.read_text(encoding="utf-8"))
            for source_data in data.get("sources", []):
                source = SourceConfig.from_dict(source_data)
                self._sources[source.name] = source
        except (json.JSONDecodeError, KeyError) as e:
            logger = __import__("oslw.config.logging", fromlist=["get_logger"]).get_logger("domain.sources.monitor")
            logger.error("Failed to load sources: %s", e)

    def _save_sources(self) -> None:
        """Save sources to JSON file."""
        import json
        self.sources_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sources": [source.to_dict() for source in self._sources.values()]
        }
        self.sources_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_sources(self) -> list[SourceConfig]:
        """List all configured sources.

        Returns:
            List of SourceConfig objects
        """
        return list(self._sources.values())

    def get_source(self, name: str) -> Optional[SourceConfig]:
        """Get a source by name.

        Args:
            name: Source name

        Returns:
            SourceConfig if found, None otherwise
        """
        return self._sources.get(name)

    def add_source(self, source: SourceConfig) -> None:
        """Add a new source.

        Args:
            source: SourceConfig to add
        """
        self._sources[source.name] = source
        self._save_sources()

    def remove_source(self, name: str) -> bool:
        """Remove a source by name.

        Args:
            name: Source name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._sources:
            del self._sources[name]
            self._save_sources()
            return True
        return False

    def monitor_all(self) -> dict:
        """Monitor all configured sources for updates.

        Returns:
            Dictionary with monitoring results per source
        """
        results = {}
        for name, source in self._sources.items():
            if not source.enabled:
                continue
            try:
                # Placeholder: in production, this would fetch from the source
                # For now, just record the check timestamp
                source.record_check(success=True)
                results[name] = {"status": "ok", "updated": 0}
            except Exception as e:
                source.record_check(success=False, error=str(e))
                results[name] = {"status": "error", "error": str(e)}
        return results
