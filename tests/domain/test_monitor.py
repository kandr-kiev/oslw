"""Tests for SourceConfig."""

import pytest
from datetime import datetime, timezone, timedelta
from oslw.domain.sources.monitor import SourceType, SourceConfig


class TestSourceType:
    """Test SourceType enum."""

    def test_source_types(self):
        """Test all source types exist."""
        assert SourceType.RSS.value == "rss"
        assert SourceType.GITHUB.value == "github"
        assert SourceType.HUGGINGFACE.value == "huggingface"
        assert SourceType.YOUTUBE.value == "youtube"
        assert SourceType.LOCAL.value == "local"


class TestSourceConfig:
    """Test SourceConfig dataclass."""

    def test_create_config(self):
        """Test creating a source config."""
        config = SourceConfig(
            name="test-source",
            type=SourceType.RSS,
            url="https://example.com/rss",
            interval_hours=12,
        )

        assert config.name == "test-source"
        assert config.type == SourceType.RSS
        assert config.url == "https://example.com/rss"
        assert config.interval_hours == 12
        assert config.enabled is True
        assert config.articles_count == 0

    def test_is_active_no_last_check(self):
        """Test is_active when never checked."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
        )

        assert config.is_active is True

    def test_is_active_disabled(self):
        """Test is_active when disabled."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
            enabled=False,
        )

        assert config.is_active is False

    def test_is_active_not_due(self):
        """Test is_active when not due for check."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
            interval_hours=6,
            last_checked=datetime.now(timezone.utc),
        )

        assert config.is_active is False

    def test_is_active_due(self):
        """Test is_active when due for check."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
            interval_hours=1,
            last_checked=datetime.now(timezone.utc) - timedelta(hours=2),
        )

        assert config.is_active is True

    def test_record_check_success(self):
        """Test recording a successful check."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
        )

        config.record_check(success=True)

        assert config.last_checked is not None
        assert config.last_error is None

    def test_record_check_failure(self):
        """Test recording a failed check."""
        config = SourceConfig(
            name="test",
            type=SourceType.RSS,
            url="https://example.com/rss",
        )

        config.record_check(success=False, error="Connection timeout")

        assert config.last_checked is not None
        assert config.last_error == "Connection timeout"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = SourceConfig(
            name="test-source",
            type=SourceType.GITHUB,
            url="https://github.com/example/repo",
            interval_hours=24,
            tags=["github", "monitoring"],
        )

        data = config.to_dict()

        assert data["name"] == "test-source"
        assert data["type"] == "github"
        assert data["url"] == "https://github.com/example/repo"
        assert data["interval_hours"] == 24
        assert data["tags"] == ["github", "monitoring"]
        assert data["enabled"] is True

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "test-source",
            "type": "huggingface",
            "url": "https://huggingface.co/models",
            "interval_hours": 12,
            "tags": ["hf", "models"],
            "articles_count": 42,
        }

        config = SourceConfig.from_dict(data)

        assert config.name == "test-source"
        assert config.type == SourceType.HUGGINGFACE
        assert config.url == "https://huggingface.co/models"
        assert config.interval_hours == 12
        assert config.tags == ["hf", "models"]
        assert config.articles_count == 42

    def test_from_dict_invalid_type_defaults(self):
        """Test from_dict with invalid type defaults to RSS."""
        data = {
            "name": "test",
            "type": "invalid_type",
            "url": "https://example.com",
        }

        config = SourceConfig.from_dict(data)
        assert config.type == SourceType.RSS

    def test_repr(self):
        """Test string representation."""
        config = SourceConfig(
            name="test-source",
            type=SourceType.YOUTUBE,
            url="https://youtube.com/feed",
        )

        repr_str = repr(config)
        assert "test-source" in repr_str
        assert "youtube" in repr_str
