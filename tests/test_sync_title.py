"""Tests for CLI sync title/tag extraction (task 2026-09-05).

Covers the two fixes:
1. ``_extract_title`` — multi-source title extraction so raw files without an
   H1 in the first 10 lines (e.g. raw HTML dumps) no longer collapse to
   "Untitled" and get skipped by slug collision.
2. ``_sync_tags`` — tags are now derived from the raw frontmatter and
   filtered against the SCHEMA.md taxonomy, replacing the hardcoded
   ``["synced"]`` (a tag absent from the taxonomy).
"""

import pytest

from oslw.cli.commands import _extract_title, _sync_tags


class TestExtractTitle:
    def test_h1_wins(self):
        content = "# Real Title\n\nbody\n"
        assert _extract_title(content, "x.md") == "Real Title"

    def test_frontmatter_title_when_no_h1(self):
        content = "---\ntitle: FM Title\n---\nbody\n"
        assert _extract_title(content, "x.md") == "FM Title"

    def test_html_title_when_no_h1_or_fm(self):
        content = (
            "<!DOCTYPE html>\n<html><head>"
            "<title>HTML Article - Example Site</title></head>"
            "<body>x</body></html>\n"
        )
        # Site suffix after " - " is stripped.
        assert _extract_title(content, "x.md") == "HTML Article"

    def test_html_entity_unescaped(self):
        content = "<html><head><title>A &amp; B</title></head></html>\n"
        assert _extract_title(content, "x.md") == "A & B"

    def test_fallback_strips_date_and_ext(self):
        assert _extract_title("no title markers here", "my-post-2026-07-23.md") == "my-post"

    def test_fallback_plain_stem(self):
        assert _extract_title("body only", "plain-name.md") == "plain-name"

    def test_empty_content_falls_back_to_name(self):
        assert _extract_title("", "fallback-name.md") == "fallback-name"


class TestSyncTags:
    def test_no_frontmatter_returns_empty(self):
        assert _sync_tags("# hi\nno tags here\n") == []

    def test_filters_to_taxonomy(self):
        # 'github' and 'release' are in the taxonomy; 'bogus-tag' is not.
        content = "---\ntags: [github, release, bogus-tag]\n---\nbody"
        out = _sync_tags(content)
        assert "github" in out
        assert "release" in out
        assert "bogus-tag" not in out

    def test_preserves_order_and_dedups(self):
        content = "---\ntags: [github, github, release]\n---\nbody"
        out = _sync_tags(content)
        assert out == [t for t in out if t in {"github", "release"}]
        assert len(out) == len(set(out))

    def test_quoted_tags_stripped(self):
        content = "---\ntags: ['github', \"release\"]\n---\nbody"
        out = _sync_tags(content)
        assert "github" in out and "release" in out
