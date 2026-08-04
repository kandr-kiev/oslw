"""SourceConfig - configuration for source monitors.

Defines source types, URLs, and monitoring parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
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
