"""Tests for slug normalization and deduplication (task t_13b3807a).

Covers the three fixes:
1. Canonical slug normalization via ``oslw.utils.slug.norm_name``.
2. Cross-category deduplication in ``FileManager.write_page``.
3. SHA256-only deduplication in ``ContentIngestor.ingest``.
4. CLI sync slug edge cases (titles with # : @ ? [ ] ( ) ,).
"""

from pathlib import Path

import pytest

from oslw.application import PageService
from oslw.domain.sources.ingest import ContentIngestor
from oslw.infrastructure.database import FileManager, PageMeta
from oslw.utils.slug import norm_name


class TestNormName:
    """Fix #1: one canonical slug for every punctuation/whitespace variant."""

    def test_lowercase_and_punctuation(self):
        assert norm_name("Release Notes: PyTorch v2.13.0") == "release-notes-pytorch-v2-13-0"

    def test_separators_collapse_to_single_hyphen(self):
        assert norm_name("Bezmezhzha --- CLI інтерфейс") == "bezmezhzha-cli-інтерфейс"
        assert norm_name("Bezmezhzha - CLI інтерфейс") == "bezmezhzha-cli-інтерфейс"
        assert norm_name("Release Notes--PyTorch v2.13.0") == "release-notes-pytorch-v2-13-0"

    def test_punctuation_stripped(self):
        assert norm_name("What? A guide @home [pdf]") == "what-a-guide-home-pdf"
        assert norm_name("issue-#123: fix bug") == "issue-123-fix-bug"
        assert norm_name("Role: Staff Engineer") == "role-staff-engineer"
        assert norm_name("C++ vs Rust (2026)") == "c-vs-rust-2026"

    def test_trim(self):
        assert norm_name("  --hello--  ") == "hello"

    def test_cyrillic_preserved(self):
        # The existing wiki keeps Cyrillic in slugs; normalization must too.
        assert norm_name("Безмежжя CLI") == "безмежжя-cli"

    def test_variants_collide(self):
        # The core bug: same concept, different punctuation must yield one slug.
        variants = [
            "role: Staff Engineer",
            "role- Staff Engineer",
            "role--Staff Engineer",
            "role-Staff-Engineer",
        ]
        slugs = {norm_name(v) for v in variants}
        assert slugs == {"role-staff-engineer"}


class TestCrossCategoryDedup:
    """Fix #2: a normalized slug is unique across ALL Layer-2 categories."""

    def test_same_normalized_slug_updates_in_place(self, tmp_path):
        ps = PageService(wiki_root=tmp_path)
        p1 = ps.create_page(
            title="Foo Bar", content="# Foo", slug="foo-bar", page_type="concept"
        )
        concept_path = p1.raw_path

        # Re-attempt the SAME slug via a different category.
        meta = PageMeta(
            slug="foo-bar",
            title="Foo Bar",
            type="comparison",
            content="# Foo v2",
            tags=[],
        )
        out = ps.file_manager.write_page(meta)

        # Must overwrite the SAME file, never create a twin in comparisons/.
        assert out == concept_path
        assert not (tmp_path / "comparisons" / "foo-bar.md").exists()
        assert len(list(tmp_path.rglob("foo-bar.md"))) == 1

    def test_identical_content_not_duplicated(self, tmp_path):
        ps = PageService(wiki_root=tmp_path)
        p1 = ps.create_page(
            title="Foo", content="# Foo", slug="foo", page_type="concept"
        )
        meta = PageMeta(
            slug="foo", title="Foo", type="concept", content="# Foo", tags=[]
        )
        out = ps.file_manager.write_page(meta)
        # Identical body -> returns existing path, writes nothing new.
        assert out == p1.raw_path
        assert len(list(tmp_path.rglob("foo.md"))) == 1

    def test_cross_category_collision_via_normalization(self, tmp_path):
        # Different slug strings that normalize identically must not create two files,
        # even when written via different Layer-2 categories.
        fm = FileManager(wiki_root=tmp_path)
        fm.write_page(PageMeta(slug="my-role:", title="A", type="concept", content="# A", tags=[]))
        fm.write_page(PageMeta(slug="my-role-", title="B", type="comparison", content="# B", tags=[]))
        found = list(tmp_path.rglob("my-role*.md"))
        # Both normalize to "my-role" -> exactly one file, in the first category.
        assert len(found) == 1
        assert found[0].stem == "my-role"
        assert found[0].parent.name == "concept"


class TestIngestSha256Dedup:
    """Fix #3: ingest skips only when the content body is byte-identical."""

    def test_identical_content_skipped(self, tmp_path):
        ing = ContentIngestor(wiki_root=tmp_path)
        r1 = ing.ingest(title="Dup Article", content="# Body", tags=[])
        assert r1.success and not r1.skipped

        r2 = ing.ingest(title="Dup Article", content="# Body", tags=[])
        assert r2.skipped is True

    def test_different_content_ingested(self, tmp_path):
        ing = ContentIngestor(wiki_root=tmp_path)
        ing.ingest(title="A", content="# A")
        r2 = ing.ingest(title="A", content="# A different")
        assert r2.success and not r2.skipped


class TestSyncSlugEdgeCases:
    """CLI ``sync`` must normalize titles with hostile punctuation."""

    def test_titles_with_punctuation_normalize_consistently(self):
        titles = [
            "Release Notes: PyTorch v2.13.0",
            "Release Notes--PyTorch v2.13.0",
            "release notes@pytorch[v2.13.0]",
        ]
        slugs = {norm_name(t) for t in titles}
        assert slugs == {"release-notes-pytorch-v2-13-0"}

    def test_existing_page_detects_normalized_title(self, tmp_path):
        """Sync should skip an article whose title matches an existing page
        after normalization (the root bug: titles with # : @ ? [ ] ( ) ,)."""
        ps = PageService(wiki_root=tmp_path)
        ps.create_page(
            title="Existing",
            content="# Existing",
            slug="release-notes-pytorch-v2-13-0",
            page_type="concept",
        )
        # A fresh raw article with a differently-punctuated title.
        existing_slugs = {norm_name(p.slug) for p in ps.file_manager.list_wiki_pages()}
        candidate = norm_name("Release Notes: PyTorch v2.13.0")
        assert candidate in existing_slugs
