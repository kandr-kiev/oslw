"""Tests for PageService - page creation and retrieval."""

from pathlib import Path

import pytest

from oslw.application import PageService
from oslw.core.exceptions import PageNotFoundError, ValidationError


@pytest.fixture
def wiki_root(tmp_path: Path) -> Path:
    """Create a temporary wiki root directory."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    return tmp_path


@pytest.fixture
def page_service(wiki_root: Path) -> PageService:
    """Create a PageService instance."""
    return PageService(wiki_root=wiki_root)


class TestPageServiceCreate:
    """Tests for page creation."""

    def test_create_page_success(self, page_service: PageService) -> None:
        """Test successful page creation."""
        page = page_service.create_page(
            title="Test Page",
            content="# Test Content\n\nThis is a test page.",
            slug="test-page",
            page_type="concept",
            tags=["test"],
        )

        assert page.slug == "test-page"
        assert page.title == "Test Page"
        assert page.type == "concept"
        assert "test" in page.tags
        assert "Test Content" in page.content

    def test_create_page_generates_slug(self, page_service: PageService) -> None:
        """Test that slug is generated from title if not provided."""
        page = page_service.create_page(
            title="My Amazing Page",
            content="# Content",
        )

        assert page.slug == "my-amazing-page"

    def test_create_page_duplicate_slug_raises(self, page_service: PageService) -> None:
        """Test that creating a page with existing slug raises ValidationError."""
        page_service.create_page(
            title="First Page",
            content="# First",
            slug="duplicate",
        )

        with pytest.raises(ValidationError, match="already exists"):
            page_service.create_page(
                title="Second Page",
                content="# Second",
                slug="duplicate",
            )

    def test_create_page_empty_title_raises(self, page_service: PageService) -> None:
        """Test that creating a page with empty title raises ValidationError."""
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            page_service.create_page(
                title="   ",
                content="# Content",
            )


class TestPageServiceGet:
    """Tests for page retrieval."""

    def test_get_page_by_slug(self, page_service: PageService) -> None:
        """Test retrieving a page by slug."""
        page_service.create_page(
            title="Retrieval Test",
            content="# Content",
            slug="retrieval-test",
        )

        page = page_service.get_page("retrieval-test")
        assert page.slug == "retrieval-test"
        assert page.title == "Retrieval Test"

    def test_get_page_not_found(self, page_service: PageService) -> None:
        """Test that retrieving a non-existent page raises PageNotFoundError."""
        with pytest.raises(PageNotFoundError, match="non-existent-page"):
            page_service.get_page("non-existent-page")


class TestPageServiceList:
    """Tests for page listing."""

    def test_list_pages_empty(self, page_service: PageService) -> None:
        """Test listing pages when none exist."""
        result = page_service.list_pages()
        assert result.pages == []
        assert result.total == 0

    def test_list_pages_with_filter(self, page_service: PageService) -> None:
        """Test filtering pages by type."""
        page_service.create_page(
            title="Concept Page",
            content="# Content",
            slug="concept-page",
            page_type="concept",
        )
        page_service.create_page(
            title="Comparison Page",
            content="# Content",
            slug="comparison-page",
            page_type="comparison",
        )

        result = page_service.list_pages(type_filter="concept")
        assert result.total == 1
        assert result.pages[0].slug == "concept-page"

    def test_list_pages_pagination(self, page_service: PageService) -> None:
        """Test pagination with limit and offset."""
        for i in range(5):
            page_service.create_page(
                title=f"Page {i}",
                content="# Content",
                slug=f"page-{i}",
            )

        result = page_service.list_pages(limit=2, offset=0)
        assert len(result.pages) == 2
        assert result.total == 5
        assert result.has_more is True

        result = page_service.list_pages(limit=2, offset=2)
        assert len(result.pages) == 2
        assert result.has_more is True

        result = page_service.list_pages(limit=2, offset=4)
        assert len(result.pages) == 1
        assert result.has_more is False
