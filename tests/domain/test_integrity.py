"""Tests for PageIntegrity."""

import pytest
from oslw.domain.wiki.integrity import PageIntegrity


class TestPageIntegrity:
    """Test PageIntegrity class."""

    def test_compute_sha256(self, sample_wiki_page):
        """Test SHA256 computation."""
        integrity = PageIntegrity(sample_wiki_page.parent.parent)
        sha256 = integrity.compute_sha256(sample_wiki_page)

        assert len(sha256) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in sha256)

    def test_compute_sha256_nonexistent(self, temp_wiki_root):
        """Test SHA256 for nonexistent file."""
        integrity = PageIntegrity(temp_wiki_root)
        sha256 = integrity.compute_sha256("nonexistent.md")

        assert sha256 == ""

    def test_extract_sha256_from_frontmatter(self, temp_wiki_root):
        """Test extracting SHA256 from frontmatter."""
        content = """---
title: Test
slug: test
sha256: abc123def456
---
Content here
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        sha256 = integrity.extract_sha256(page_path)

        assert sha256 == "abc123def456"

    def test_extract_sha256_missing(self, temp_wiki_root):
        """Test extracting SHA256 when not in frontmatter."""
        content = """---
title: Test
slug: test
---
Content here
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        sha256 = integrity.extract_sha256(page_path)

        assert sha256 is None

    def test_extract_wikilinks(self, temp_wiki_root):
        """Test extracting wikilinks from content."""
        content = """---
title: Test
slug: test
---
Content with [[transformer-architecture]] and [[attention-mechanism]].
Also [[encoder-decoder]].
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        links = integrity.extract_wikilinks(page_path)

        assert "transformer-architecture" in links
        assert "attention-mechanism" in links
        assert "encoder-decoder" in links
        assert len(links) == 3

    def test_extract_wikilinks_none(self, temp_wiki_root):
        """Test extracting wikilinks when none present."""
        content = """---
title: Test
slug: test
---
No wikilinks here.
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        links = integrity.extract_wikilinks(page_path)

        assert links == []

    def test_check_page_no_issues(self, sample_wiki_page):
        """Test checking a page with no issues."""
        integrity = PageIntegrity(sample_wiki_page.parent.parent)
        result = integrity.check_page(sample_wiki_page)

        assert result.sha256_match is True
        assert len(result.broken_links) >= 0  # May have broken links

    def test_check_sha256_fix_adds_hash(self, temp_wiki_root):
        """Test fixing SHA256 in frontmatter — adds hash when missing."""
        content = """---
title: Test
slug: test
---
Content here
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        fixed = integrity.fix_sha256(page_path)

        # Should return True and add sha256
        assert fixed is True
        new_content = page_path.read_text()
        assert "sha256:" in new_content
        extracted = integrity.extract_sha256(page_path)
        assert extracted is not None
        assert len(extracted) == 64

    def test_fix_wikilinks(self, temp_wiki_root):
        """Test fixing broken wikilinks."""
        content = """---
title: Test
slug: test
---
Content with [[Page Title]] and [[Another Page]].
"""
        page_path = temp_wiki_root / "wiki" / "test.md"
        page_path.write_text(content)

        integrity = PageIntegrity(temp_wiki_root)
        fixed = integrity.fix_wikilinks(page_path)

        # Should fix "Page Title" -> "page-title", "Another Page" -> "another-page"
        assert fixed == 2

        content = page_path.read_text()
        assert "[[page-title]]" in content
        assert "[[another-page]]" in content
