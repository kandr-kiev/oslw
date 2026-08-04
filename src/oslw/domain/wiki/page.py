"""WikiPage model - represents a single wiki page."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from oslw.core.exceptions import PageValidationError


# ============================================================================
# Page types
# ============================================================================

class PageType(str, Enum):
    """Valid wiki page types."""

    CONCEPT = "concept"
    COMPARISON = "comparison"
    PLAYBOOK = "playbook"
    SYNTHESIS = "synthesis"
    ENTITY = "entity"
    EVENT = "event"

    @classmethod
    def valid_types(cls) -> set[str]:
        return {t.value for t in cls}


# ============================================================================
# WikiPage dataclass
# ============================================================================

@dataclass
class WikiPage:
    """Represents a single wiki page with frontmatter and content.

    Attributes:
        slug: URL-friendly identifier (e.g., "transformers-architecture")
        title: Human-readable title
        description: Short description
        type: Page category (concept, comparison, etc.)
        tags: List of tags for categorization
        sources: List of source URLs
        confidence: Confidence score (0.0-1.0)
        links: List of related page slugs
        created: Creation timestamp
        updated: Last update timestamp
        content: Markdown content (without frontmatter)
        raw_path: Path to the raw article source (if any)
        line_count: Number of content lines
        word_count: Number of words
    """

    slug: str
    title: str
    description: str = ""
    type: PageType = PageType.CONCEPT
    tags: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.5
    links: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    content: str = ""
    raw_path: Optional[Path] = None
    line_count: int = 0
    word_count: int = 0

    # Computed properties
    @property
    def filename(self) -> str:
        """Generate filename from slug."""
        return f"{self.slug}.md"

    @property
    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate page data.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Slug validation
        if not self.slug:
            errors.append("Slug is required")
        elif not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', self.slug):
            errors.append(f"Invalid slug format: {self.slug}")

        # Title validation
        if not self.title:
            errors.append("Title is required")

        # Type validation
        if self.type not in PageType.valid_types():
            errors.append(f"Invalid page type: {self.type}")

        # Content validation
        if not self.content or len(self.content.strip()) < 10:
            errors.append("Content must be at least 10 characters")

        return len(errors) == 0, errors

    def validate_required(self) -> None:
        """Validate required fields, raise PageValidationError on failure."""
        is_valid, errors = self.is_valid
        if not is_valid:
            raise PageValidationError(self.slug, errors)

    def update_from_dict(self, data: dict) -> None:
        """Update page fields from a dictionary.

        Args:
            data: Dictionary of field names to values
        """
        updatable = {
            "title", "description", "type", "tags", "sources",
            "confidence", "links", "content",
        }

        for key, value in data.items():
            if key in updatable and hasattr(self, key):
                if key == "type" and isinstance(value, str):
                    try:
                        setattr(self, key, PageType(value))
                    except ValueError:
                        pass
                else:
                    setattr(self, key, value)

        self.updated = datetime.now()

    def to_dict(self) -> dict:
        """Serialize page to dictionary."""
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "tags": self.tags,
            "sources": self.sources,
            "confidence": self.confidence,
            "links": self.links,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "content": self.content,
            "line_count": self.line_count,
            "word_count": self.word_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WikiPage:
        """Create WikiPage from dictionary.

        Args:
            data: Dictionary with page fields

        Returns:
            WikiPage instance
        """
        type_val = data.get("type", "concept")
        if isinstance(type_val, str):
            try:
                type_val = PageType(type_val)
            except ValueError:
                type_val = PageType.CONCEPT

        created = data.get("created")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        updated = data.get("updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)

        return cls(
            slug=data["slug"],
            title=data["title"],
            description=data.get("description", ""),
            type=type_val,
            tags=data.get("tags", []),
            sources=data.get("sources", []),
            confidence=data.get("confidence", 0.5),
            links=data.get("links", []),
            created=created or datetime.now(),
            updated=updated or datetime.now(),
            content=data.get("content", ""),
            raw_path=data.get("raw_path"),
            line_count=data.get("line_count", 0),
            word_count=data.get("word_count", 0),
        )

    def __repr__(self) -> str:
        return f"WikiPage(slug='{self.slug}', title='{self.title}', type={self.type.value})"
