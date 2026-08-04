"""Tests for WikiPage model."""

import pytest
from oslw.domain.wiki.page import WikiPage, PageType
from oslw.core.exceptions import PageValidationError


class TestWikiPage:
    """Test WikiPage dataclass and validation."""

    def test_create_valid_page(self):
        """Test creating a valid WikiPage."""
        page = WikiPage(
            slug="transformer-architecture",
            title="Transformer Architecture",
            description="The Transformer architecture",
            type=PageType.CONCEPT,
            tags=["transformers", "nlp"],
            content="The Transformer is a neural network architecture...",
        )

        assert page.slug == "transformer-architecture"
        assert page.title == "Transformer Architecture"
        assert page.type == PageType.CONCEPT
        assert page.tags == ["transformers", "nlp"]
        assert page.filename == "transformer-architecture.md"

    def test_page_validation_valid(self):
        """Test validation of a valid page."""
        page = WikiPage(
            slug="valid-slug",
            title="Valid Page",
            content="This is valid content that is long enough.",
        )

        is_valid, errors = page.is_valid
        assert is_valid is True
        assert len(errors) == 0

    def test_page_validation_missing_slug(self):
        """Test validation fails without slug."""
        page = WikiPage(
            slug="",
            title="Invalid Page",
            content="Missing slug.",
        )

        is_valid, errors = page.is_valid
        assert is_valid is False
        assert any("Slug is required" in e for e in errors)

    def test_page_validation_invalid_slug_format(self):
        """Test validation fails with invalid slug format."""
        page = WikiPage(
            slug="Invalid-Slug-With-Caps",
            title="Invalid Page",
            content="Invalid slug format.",
        )

        is_valid, errors = page.is_valid
        assert is_valid is False
        assert any("Invalid slug format" in e for e in errors)

    def test_page_validation_missing_title(self):
        """Test validation fails without title."""
        page = WikiPage(
            slug="no-title",
            title="",
            content="Missing title.",
        )

        is_valid, errors = page.is_valid
        assert is_valid is False
        assert any("Title is required" in e for e in errors)

    def test_page_validation_short_content(self):
        """Test validation fails with short content."""
        page = WikiPage(
            slug="short-content",
            title="Short Content",
            content="Too short",
        )

        is_valid, errors = page.is_valid
        assert is_valid is False
        assert any("at least 10 characters" in e for e in errors)

    def test_validate_required_raises(self):
        """Test validate_required raises on invalid page."""
        page = WikiPage(
            slug="",
            title="",
            content="",
        )

        with pytest.raises(PageValidationError):
            page.validate_required()

    def test_validate_required_passes(self):
        """Test validate_required passes on valid page."""
        page = WikiPage(
            slug="valid-page",
            title="Valid Page",
            content="This is valid content that is long enough.",
        )

        # Should not raise
        page.validate_required()

    def test_update_from_dict(self):
        """Test updating page from dictionary."""
        page = WikiPage(
            slug="test-page",
            title="Test Page",
            content="Test content.",
        )

        page.update_from_dict({
            "title": "Updated Title",
            "tags": ["new", "tags"],
            "confidence": 0.9,
        })

        assert page.title == "Updated Title"
        assert page.tags == ["new", "tags"]
        assert page.confidence == 0.9

    def test_to_dict(self):
        """Test serialization to dictionary."""
        page = WikiPage(
            slug="test-page",
            title="Test Page",
            type=PageType.PLAYBOOK,
            tags=["test"],
            content="Test content.",
        )

        data = page.to_dict()

        assert data["slug"] == "test-page"
        assert data["title"] == "Test Page"
        assert data["type"] == "playbook"
        assert data["tags"] == ["test"]
        assert data["content"] == "Test content."

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "slug": "test-page",
            "title": "Test Page",
            "type": "concept",
            "tags": ["test", "example"],
            "content": "Test content.",
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T12:00:00",
        }

        page = WikiPage.from_dict(data)

        assert page.slug == "test-page"
        assert page.title == "Test Page"
        assert page.type == PageType.CONCEPT
        assert page.tags == ["test", "example"]
        assert page.content == "Test content."

    def test_from_dict_invalid_type_defaults(self):
        """Test from_dict with invalid type defaults to CONCEPT."""
        data = {
            "slug": "test-page",
            "title": "Test Page",
            "type": "invalid_type",
            "content": "Test content.",
        }

        page = WikiPage.from_dict(data)
        assert page.type == PageType.CONCEPT

    def test_repr(self):
        """Test string representation."""
        page = WikiPage(
            slug="test-page",
            title="Test Page",
            type=PageType.CONCEPT,
        )

        repr_str = repr(page)
        assert "test-page" in repr_str
        assert "Test Page" in repr_str
        assert "concept" in repr_str
