"""Tests for content scanners - RSS, GitHub, HuggingFace, YouTube."""

import hashlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from oslw.domain.sources.scanners import (
    GitHubScanner,
    HuggingFaceScanner,
    RawArticle,
    RSSScanner,
    YouTubeScanner,
)


class FakeFeedEntry:
    """Fake feedparser entry with dict-like access."""

    def __init__(self, data: dict):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]

    @property
    def title(self):
        return self._data.get("title", "")

    @property
    def summary(self):
        return self._data.get("summary", "")

    @property
    def description(self):
        return self._data.get("description", self._data.get("summary", ""))

    @property
    def link(self):
        return self._data.get("link", "")

    @property
    def id(self):
        return self._data.get("id", self._data.get("guid", ""))

    @property
    def guid(self):
        return self._data.get("guid", self._data.get("id", ""))

    @property
    def published(self):
        return self._data.get("published", "")

    @property
    def author(self):
        return self._data.get("author", "")

    @property
    def links(self):
        return self._data.get("links", [])


class FakeFeed:
    """Fake feedparser feed result."""

    def __init__(self, entries: list, bozo: bool = False, bozo_exception=None):
        self.entries = entries
        self.bozo = bozo
        self.bozo_exception = bozo_exception
        self.feed = {"title": "Test Feed"}


class TestRawArticle:
    """Tests for RawArticle dataclass."""

    def test_create_article(self):
        article = RawArticle(
            title="Test Article",
            slug="test-article",
            content="# Test\n\nContent here.",
            url="https://example.com/test",
            source_name="test-source",
            tags=["test"],
        )
        assert article.title == "Test Article"
        assert article.slug == "test-article"
        assert article.source_name == "test-source"
        assert article.tags == ["test"]
        assert len(article.content_hash) == 16

    def test_content_hash_deterministic(self):
        a1 = RawArticle(
            title="Test", slug="test", content="Content", url="https://x.com"
        )
        a2 = RawArticle(
            title="Test", slug="test", content="Content", url="https://x.com"
        )
        assert a1.content_hash == a2.content_hash

    def test_content_hash_different_content(self):
        a1 = RawArticle(
            title="Test", slug="test", content="Content A", url="https://x.com"
        )
        a2 = RawArticle(
            title="Test", slug="test", content="Content B", url="https://x.com"
        )
        assert a1.content_hash != a2.content_hash


class TestRSSScanner:
    """Tests for RSSScanner."""

    @patch("feedparser.parse")
    def test_fetch_single_entry(self, mock_parse):
        mock_parse.return_value = FakeFeed([
            FakeFeedEntry({
                "title": "Test RSS Article",
                "summary": "This is a test summary",
                "link": "https://example.com/article",
                "published": "Thu, 06 Aug 2026 12:00:00 GMT",
                "author": "John Doe",
            })
        ])

        scanner = RSSScanner()
        articles = scanner.fetch(
            url="https://example.com/feed.xml",
            source_name="test-rss",
            tags=["test"],
            limit=10,
        )

        assert len(articles) == 1
        assert articles[0].title == "Test RSS Article"
        assert articles[0].source_name == "test-rss"
        assert "test" in articles[0].tags
        assert "https://example.com/article" in articles[0].content

    @patch("feedparser.parse")
    def test_fetch_empty_feed(self, mock_parse):
        mock_parse.return_value = FakeFeed([])

        scanner = RSSScanner()
        articles = scanner.fetch(
            url="https://example.com/feed.xml",
            source_name="test-rss",
            tags=[],
        )

        assert articles == []

    @patch("feedparser.parse")
    def test_fetch_parse_error(self, mock_parse):
        mock_parse.return_value = FakeFeed([], bozo=True, bozo_exception="Error")

        scanner = RSSScanner()
        articles = scanner.fetch(
            url="https://example.com/feed.xml",
            source_name="test-rss",
            tags=[],
        )

        assert articles == []

    def test_clean_text(self):
        scanner = RSSScanner()
        assert scanner._clean_text("<b>Bold</b> text") == "Bold text"
        assert scanner._clean_text("") == ""
        assert scanner._clean_text(None) == ""

    def test_generate_slug(self):
        scanner = RSSScanner()
        assert scanner._generate_slug("Hello World") == "hello-world"
        assert scanner._generate_slug("Test   Multiple   Spaces") == "test-multiple-spaces"
        assert scanner._generate_slug("Special @#$ Chars!") == "special-chars"

    def test_generate_slug_short(self):
        scanner = RSSScanner()
        slug = scanner._generate_slug("A")
        assert slug.startswith("rss-")

    @patch("feedparser.parse")
    def test_fetch_with_author_and_date(self, mock_parse):
        mock_parse.return_value = FakeFeed([
            FakeFeedEntry({
                "title": "Test with Author",
                "summary": "Summary here",
                "link": "https://example.com/test",
                "published": "Thu, 06 Aug 2026 12:00:00 GMT",
                "author": "Jane Smith",
            })
        ])

        scanner = RSSScanner()
        articles = scanner.fetch(
            url="https://example.com/feed.xml",
            source_name="test",
            tags=["test"],
        )

        assert articles[0].author == "Jane Smith"
        assert articles[0].published is not None
        assert "Jane Smith" in articles[0].content
        assert "2026-08-06" in articles[0].content

    def test_parse_published(self):
        scanner = RSSScanner()
        dt = scanner._parse_published("Thu, 06 Aug 2026 12:00:00 GMT")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 8
        assert dt.day == 6

    def test_parse_published_empty(self):
        scanner = RSSScanner()
        assert scanner._parse_published("") is None
        assert scanner._parse_published(None) is None


class TestGitHubScanner:
    """Tests for GitHubScanner."""

    @patch("requests.get")
    def test_fetch_releases(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "v1.0.0 Release",
                "tag_name": "v1.0.0",
                "body": "Major release with new features",
                "html_url": "https://github.com/owner/repo/releases/tag/v1.0.0",
                "published_at": "2026-08-06T12:00:00Z",
            }
        ]
        mock_get.return_value = mock_response

        scanner = GitHubScanner()
        articles = scanner.fetch(
            repo="owner/repo",
            source_name="test-github",
            tags=["github"],
        )

        assert len(articles) == 1
        assert "v1.0.0" in articles[0].title
        assert "owner/repo" in articles[0].content
        assert "github" in articles[0].tags

    @patch("requests.get")
    def test_fetch_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        scanner = GitHubScanner()
        articles = scanner.fetch(
            repo="owner/nonexistent",
            source_name="test",
            tags=[],
        )

        assert articles == []

    @patch("requests.get")
    def test_fetch_no_releases(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        scanner = GitHubScanner()
        articles = scanner.fetch(
            repo="owner/repo",
            source_name="test",
            tags=[],
        )

        assert articles == []

    def test_generate_slug(self):
        scanner = GitHubScanner()
        assert scanner._generate_slug("Release v1.0.0") == "release-v1-0-0"


class TestHuggingFaceScanner:
    """Tests for HuggingFaceScanner."""

    @patch("requests.get")
    def test_fetch_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "test-org/test-model",
                "modelId": "test-org/test-model",
                "downloads": 1000,
                "likes": 50,
                "tags": ["transformers", "text-generation"],
                "pipeline_tag": "text-classification",
            }
        ]
        mock_get.return_value = mock_response

        scanner = HuggingFaceScanner()
        articles = scanner.fetch(
            source_name="hf-test",
            tags=["huggingface"],
            limit=5,
        )

        assert len(articles) == 1
        assert "test-org/test-model" in articles[0].title
        assert "https://huggingface.co/test-org/test-model" in articles[0].url
        assert "huggingface" in articles[0].tags

    @patch("requests.get")
    def test_fetch_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        scanner = HuggingFaceScanner()
        articles = scanner.fetch(
            source_name="hf-test",
            tags=[],
        )

        assert articles == []


class TestYouTubeScanner:
    """Tests for YouTubeScanner."""

    @patch("feedparser.parse")
    def test_fetch_videos(self, mock_parse):
        mock_parse.return_value = FakeFeed([
            FakeFeedEntry({
                "title": "Test YouTube Video",
                "link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "published": "2026-08-06T12:00:00+00:00",
                "author": "Channel Name",
                "summary": "Video description here",
            })
        ])

        scanner = YouTubeScanner()
        articles = scanner.fetch(
            channel_id="UC29ju8bIPH5as8OGn4zwJ8A",
            source_name="yt-test",
            tags=["youtube"],
        )

        assert len(articles) == 1
        assert "Test YouTube Video" in articles[0].title
        assert "dQw4w9WgXcQ" in articles[0].url
        assert "youtube" in articles[0].tags

    @patch("feedparser.parse")
    def test_fetch_empty_feed(self, mock_parse):
        mock_parse.return_value = FakeFeed([])

        scanner = YouTubeScanner()
        articles = scanner.fetch(
            channel_id="UC29ju8bIPH5as8OGn4zwJ8A",
            source_name="yt-test",
            tags=[],
        )

        assert articles == []

    def test_clean_text(self):
        scanner = YouTubeScanner()
        assert scanner._clean_text("<div>Test</div>") == "Test"
        assert scanner._clean_text("") == ""


class TestSourceMonitorIntegration:
    """Integration tests for SourceMonitor with scanners."""

    def test_monitor_all_with_sources(self):
        """Test that monitor_all loads sources and processes them."""
        from oslw.domain.sources.monitor import SourceMonitor

        monitor = SourceMonitor(wiki_root="/workspace/llm-wiki")
        sources = monitor.list_sources()

        # Sources loaded from config/sources.json (count grows over time —
        # don't hardcode it; just require a non-trivial config).
        assert len(sources) >= 5

        # Verify enabled sources
        enabled = [s for s in sources if s.enabled]
        assert len(enabled) > 0

        # Verify disabled sources
        disabled = [s for s in sources if not s.enabled]
        assert len(disabled) > 0

    def test_monitor_all_fetches_rss(self):
        """Test that monitor_all actually fetches from RSS sources."""
        from oslw.domain.sources.monitor import SourceMonitor

        monitor = SourceMonitor(wiki_root="/workspace/llm-wiki")
        results = monitor.monitor_all()

        # Should have results for all enabled sources
        enabled_count = sum(1 for s in monitor.list_sources() if s.enabled)
        assert len(results) == enabled_count

        # RSS sources should have fetched articles
        for name, result in results.items():
            if result["status"] == "ok":
                assert "updated" in result
                assert "total_fetched" in result
                assert result["updated"] >= 0
                assert result["total_fetched"] >= 0

    def test_add_and_remove_source(self):
        """Test adding and removing sources."""
        from oslw.domain.sources.monitor import SourceMonitor, SourceConfig, SourceType

        monitor = SourceMonitor(wiki_root="/workspace/llm-wiki")
        initial_count = len(monitor.list_sources())

        # Add a source
        new_source = SourceConfig(
            name="test-add-source",
            type=SourceType.RSS,
            url="https://example.com/feed.xml",
            tags=["test"],
        )
        monitor.add_source(new_source)
        assert len(monitor.list_sources()) == initial_count + 1

        # Remove it
        removed = monitor.remove_source("test-add-source")
        assert removed is True
        assert len(monitor.list_sources()) == initial_count

        # Remove non-existent
        removed = monitor.remove_source("non-existent")
        assert removed is False

    def test_get_source(self):
        """Test getting a specific source."""
        from oslw.domain.sources.monitor import SourceMonitor

        monitor = SourceMonitor(wiki_root="/workspace/llm-wiki")
        source = monitor.get_source("bbc-news")
        assert source is not None
        assert source.name == "bbc-news"
        assert source.type.value == "rss"

        non_existent = monitor.get_source("non-existent")
        assert non_existent is None
