"""Canonical slug normalization for OSLW.

Single source of truth for turning arbitrary titles/file names into the
filesystem-safe slugs used across the wiki. Every slug producer
(scanners, ingestor, page model, CLI sync) must route through :func:`norm_name`
so that the same concept always yields the same file name — regardless of which
punctuation, casing or whitespace variation appeared in the source title.

Design (matches the audit etalon from the 2026-08-25 session):

    re.sub(r'[^\\w\\u0400-\\u04ff]+', '-', s)

- ``\\w`` (unicode) keeps ``a-z``, ``0-9`` and ASCII word chars.
- ``\\u0400-\\u04ff`` keeps Cyrillic, which the existing wiki already uses in
  file names (e.g. ``безмежжя-cli-інтерфейс.md``).
- Every run of characters that is NOT word/Cyrillic (spaces, ``# : @ ? [ ] ( ) ,
  .`` etc.) collapses to a single ``-``.
- Leading/trailing hyphens are trimmed.

This is what makes ``безмежжя---cli-інтерфейс`` and ``безмежжя-cli-інтерфейс``
(and ``role:`` vs ``role-``) collide to the same file instead of spawning
duplicates.
"""

from __future__ import annotations

import re

# Word chars (unicode) + full Cyrillic block.
_SLUG_STRIP_RE = re.compile(r"[^\w\u0400-\u04ff]+")
_HYPHEN_RE = re.compile(r"-+")


def norm_name(title: str) -> str:
    """Normalize an arbitrary title into a canonical wiki slug.

    Args:
        title: Raw title or file-stem.

    Returns:
        Lowercase slug with non-word/Cyrillic runs collapsed to single hyphens,
        hyphens collapsed and trimmed. Empty string if the input has no usable
        characters (callers should substitute a timestamped fallback).
    """
    if not title:
        return ""
    slug = title.lower().strip()
    slug = _SLUG_STRIP_RE.sub("-", slug)
    slug = _HYPHEN_RE.sub("-", slug).strip("-")
    return slug
