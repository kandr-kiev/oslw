"""Tests for WikiIndex."""

import pytest
from pathlib import Path
from oslw.domain.wiki.index import WikiIndex, IndexEntry, WikiIndexError


class TestWikiIndex:
    """Test WikiIndex class."""

    def test_load_empty_index(self, temp_wiki_root):
        """Test loading an empty index file."""
        index_path = temp_wiki_root / "wiki" / "index.md"
        index_path.write_text("# LLM-Wiki Index\n\n")

        index = WikiIndex(temp_wiki_root)
        index.load()

        assert len(index) == 0
        assert index.get_all_slugs() == []

    def test_load_index_with_entries(self, temp_wiki_root):
        """Test loading index with entries."""
        index_content = """# LLM-Wiki Index

### transformer-architecture [wiki/concepts/transformer-architecture.md]
### attention-mechanism [wiki/concepts/attention-mechanism.md]
### encoder-decoder [wiki/comparisons/encoder-decoder.md]
"""
        index_path = temp_wiki_root / "wiki" / "index.md"
        index_path.write_text(index_content)

        index = WikiIndex(temp_wiki_root)
        index.load()

        assert len(index) == 3
        assert "transformer-architecture" in index.entries
        assert "attention-mechanism" in index.entries
        assert "encoder-decoder" in index.entries

    def test_load_nonexistent_index(self, temp_wiki_root):
        """Test loading index when file doesn't exist."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        # Should not raise, just empty
        assert len(index) == 0

    def test_add_entry(self, temp_wiki_root):
        """Test adding an entry to the index."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("test-page", "wiki/concepts/test-page.md", "A test page")

        assert len(index) == 1
        assert index.has_entry("test-page")

        entry = index.get_entry("test-page")
        assert entry is not None
        assert entry.path == "wiki/concepts/test-page.md"
        assert entry.description == "A test page"

    def test_remove_entry(self, temp_wiki_root):
        """Test removing an entry from the index."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("test-page", "wiki/concepts/test-page.md")
        assert index.has_entry("test-page")

        removed = index.remove_entry("test-page")
        assert removed is True
        assert not index.has_entry("test-page")

    def test_remove_nonexistent_entry(self, temp_wiki_root):
        """Test removing a non-existent entry."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        removed = index.remove_entry("nonexistent")
        assert removed is False

    def test_update_entry(self, temp_wiki_root):
        """Test updating an existing entry."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("test-page", "old-path.md")
        index.update_entry("test-page", "new-path.md", "Updated description")

        entry = index.get_entry("test-page")
        assert entry.path == "new-path.md"
        assert entry.description == "Updated description"

    def test_update_nonexistent_creates(self, temp_wiki_root):
        """Test updating a non-existent entry creates it."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.update_entry("new-page", "new-path.md")
        assert index.has_entry("new-page")

    def test_save_index(self, temp_wiki_root):
        """Test saving index to file."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("alpha-page", "wiki/concepts/alpha.md")
        index.add_entry("beta-page", "wiki/concepts/beta.md")
        index.save()

        # Verify file was written
        index_path = temp_wiki_root / "wiki" / "index.md"
        assert index_path.exists()

        content = index_path.read_text()
        assert "### alpha-page [wiki/concepts/alpha.md]" in content
        assert "### beta-page [wiki/concepts/beta.md]" in content

    def test_save_preserves_order(self, temp_wiki_root):
        """Test that saved index is sorted by slug."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("zebra", "wiki/concepts/zebra.md")
        index.add_entry("alpha", "wiki/concepts/alpha.md")
        index.add_entry("mango", "wiki/concepts/mango.md")
        index.save()

        index2 = WikiIndex(temp_wiki_root)
        index2.load()

        slugs = index2.get_all_slugs()
        assert slugs == ["alpha", "mango", "zebra"]

    def test_count(self, temp_wiki_root):
        """Test counting entries."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("page-1", "wiki/concepts/page-1.md")
        index.add_entry("page-2", "wiki/concepts/page-2.md")

        assert index.count() == 2
        assert len(index) == 2

    def test_get_all_slugs(self, temp_wiki_root):
        """Test getting all slugs."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("gamma", "wiki/concepts/gamma.md")
        index.add_entry("alpha", "wiki/concepts/alpha.md")
        index.add_entry("beta", "wiki/concepts/beta.md")

        slugs = index.get_all_slugs()
        assert slugs == ["alpha", "beta", "gamma"]

    def test_repr(self, temp_wiki_root):
        """Test string representation."""
        index = WikiIndex(temp_wiki_root)
        index.load()

        index.add_entry("test", "wiki/concepts/test.md")
        repr_str = repr(index)
        assert "entries=1" in repr_str
        assert "index.md" in repr_str
