"""Domain events for OSLW.

Events are used for internal communication between modules
and for audit logging.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of domain events."""

    # Wiki events
    PAGE_CREATED = "page.created"
    PAGE_UPDATED = "page.updated"
    PAGE_DELETED = "page.deleted"
    PAGE_DUPLICATED = "page.duplicated"
    PAGE_FIXED = "page.fixed"

    # Source events
    SOURCE_FETCHED = "source.fetched"
    SOURCE_ERROR = "source.error"
    ARTICLE_INGESTED = "article.ingested"

    # Graph events
    GRAPH_GENERATED = "graph.generated"
    GRAPH_QUERY = "graph.query"

    # Quality events
    DOCTOR_DIAGNOSED = "doctor.diagnosed"
    DOCTOR_CURED = "doctor.cured"
    LINT_FOUND = "lint.found"

    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_SHUTDOWN = "system.shutdown"


@dataclass
class DomainEvent:
    """Base domain event."""

    event_type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dict."""
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class PageCreatedEvent(DomainEvent):
    """Event when a wiki page is created."""

    event_type: EventType = EventType.PAGE_CREATED
    slug: str = ""
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["slug"] = self.slug
        d["title"] = self.title
        return d


@dataclass
class PageUpdatedEvent(DomainEvent):
    """Event when a wiki page is updated."""

    event_type: EventType = EventType.PAGE_UPDATED
    slug: str = ""
    changes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["slug"] = self.slug
        d["changes"] = self.changes
        return d


@dataclass
class DoctorDiagnosedEvent(DomainEvent):
    """Event when WikiDoctor completes a diagnosis."""

    event_type: EventType = EventType.DOCTOR_DIAGNOSED
    total_pages: int = 0
    errors: int = 0
    warnings: int = 0
    fixes_applied: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["total_pages"] = self.total_pages
        d["errors"] = self.errors
        d["warnings"] = self.warnings
        d["fixes_applied"] = self.fixes_applied
        return d
