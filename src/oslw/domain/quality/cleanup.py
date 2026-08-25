"""Deduplication - detect and remove duplicate wiki pages.

Provides:
- SHA256-based duplicate detection
- _N suffix cleanup
- Content similarity detection
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger

logger = get_logger("domain.quality.cleanup")


@dataclass
class DuplicateGroup:
    """Group of duplicate pages.

    Attributes:
        base_slug: The canonical slug (kept version)
        duplicates: List of duplicate slugs to remove
        sha256: SHA256 hash of the content
        reason: Why they're considered duplicates
    """

    base_slug: str
    duplicates: list[str] = field(default_factory=list)
    sha256: str = ""
    reason: str = "content_match"


class Deduplication:
    """Wiki page deduplication engine.

    Provides:
    - SHA256-based duplicate detection
    - _N suffix cleanup
    - Content similarity detection

    Usage:
        from oslw.config import settings
        dedup = Deduplication(wiki_root=settings.wiki_root)
        groups = dedup.find_duplicates()
        for group in groups:
            print(f"Base: {group.base_slug}")
            print(f"Duplicates: {group.duplicates}")
    """

    def __init__(self, wiki_root: str | Path):
        """Initialize Deduplication.

        Args:
            wiki_root: Path to wiki root directory (from Settings, not hardcoded)
        """
        self.wiki_root = Path(wiki_root)

    def find_duplicates(self) -> list[DuplicateGroup]:
        """Find all duplicates using all detection methods.

        Returns:
            Combined list of DuplicateGroup from all methods
        """
        wiki_dir = self.wiki_root
        if not wiki_dir.exists():
            logger.warning("Директорію wiki не знайдено: %s", wiki_dir)
            return []

        # Run all three detection methods
        suffix_groups = self.find_duplicates_by_suffix(wiki_dir)
        sha_groups = self.find_duplicates_by_sha256(wiki_dir)
        sim_groups = self.find_duplicates_by_similarity(wiki_dir)

        all_groups = suffix_groups + sha_groups + sim_groups
        logger.info(
            "Знайдено %d груп дублікатів (suffix: %d, sha256: %d, similarity: %d)",
            len(all_groups), len(suffix_groups), len(sha_groups), len(sim_groups),
        )
        return all_groups

    def find_duplicates_by_suffix(self, dir_path: str | Path) -> list[DuplicateGroup]:
        """Find duplicates by _N suffix pattern.

        Args:
            dir_path: Directory to scan

        Returns:
            List of DuplicateGroup
        """
        path = Path(dir_path)
        if not path.exists():
            return []

        # Group files by base name
        base_names: dict[str, list[Path]] = {}

        for md_file in path.glob("*.md"):
            match = re.match(r'^(.+)_\d+\.md$', md_file.name)
            if match:
                base = match.group(1)
                if base not in base_names:
                    base_names[base] = []
                base_names[base].append(md_file)

        groups = []
        for base, versions in base_names.items():
            # Sort by suffix number
            versions.sort(key=lambda p: int(re.search(r'_(\d+)$', p.stem).group(1)))

            # Check if base version exists
            base_file = path / f"{base}.md"
            if base_file.exists():
                # Delete all _N versions
                groups.append(DuplicateGroup(
                    base_slug=base,
                    duplicates=[v.stem for v in versions],
                    reason="suffix_duplicate",
                ))
            else:
                # Keep highest _N, delete rest
                keep = versions[-1]
                groups.append(DuplicateGroup(
                    base_slug=base,
                    duplicates=[v.stem for v in versions[:-1]],
                    reason="suffix_only_versions",
                ))

        logger.info(
            "Знайдено %d груп дублікатів by suffix in %s",
            len(groups),
            path,
        )
        return groups

    def find_duplicates_by_sha256(self, dir_path: str | Path) -> list[DuplicateGroup]:
        """Find duplicates by SHA256 content hash.

        Args:
            dir_path: Directory to scan

        Returns:
            List of DuplicateGroup
        """
        path = Path(dir_path)
        if not path.exists():
            return []

        # Compute SHA256 for all files
        hashes: dict[str, list[Path]] = {}

        for md_file in path.rglob("*.md"):
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue

            # Read content (strip frontmatter)
            text = md_file.read_text(encoding="utf-8")
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    text = parts[2]

            sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

            if sha256 not in hashes:
                hashes[sha256] = []
            hashes[sha256].append(md_file)

        # Find groups with multiple files
        groups = []
        for sha256, files in hashes.items():
            if len(files) > 1:
                # Keep first, mark rest as duplicates
                groups.append(DuplicateGroup(
                    base_slug=files[0].stem,
                    duplicates=[f.stem for f in files[1:]],
                    sha256=sha256,
                    reason="content_match",
                ))

        logger.info(
            "Знайдено %d груп дублікатів by SHA256 in %s",
            len(groups),
            path,
        )
        return groups

    def find_duplicates_by_similarity(self, dir_path: str | Path, threshold: float = 0.85) -> list[DuplicateGroup]:
        """Find duplicates by content similarity.

        Uses simple token overlap ratio.

        Args:
            dir_path: Directory to scan
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of DuplicateGroup
        """
        path = Path(dir_path)
        if not path.exists():
            return []

        # Read all files and compute tokens
        files_data: dict[Path, set[str]] = {}

        for md_file in path.rglob("*.md"):
            if md_file.name in ("index.md", "SCHEMA.md"):
                continue

            text = md_file.read_text(encoding="utf-8")
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    text = parts[2]

            # Simple tokenization
            tokens = set(re.findall(r'\b\w+\b', text.lower()))
            files_data[md_file] = tokens

        # Compare all pairs
        file_list = list(files_data.keys())
        groups = []
        processed = set()

        for i in range(len(file_list)):
            if file_list[i] in processed:
                continue

            for j in range(i + 1, len(file_list)):
                if file_list[j] in processed:
                    continue

                tokens_a = files_data[file_list[i]]
                tokens_b = files_data[file_list[j]]

                if not tokens_a or not tokens_b:
                    continue

                # Jaccard similarity
                intersection = len(tokens_a & tokens_b)
                union = len(tokens_a | tokens_b)
                similarity = intersection / union if union > 0 else 0.0

                if similarity >= threshold:
                    base = file_list[i]
                    dup = file_list[j]
                    groups.append(DuplicateGroup(
                        base_slug=base.stem,
                        duplicates=[dup.stem],
                        reason=f"similarity_{similarity:.2f}",
                    ))
                    processed.add(dup)

        logger.info(
            "Знайдено %d груп дублікатів by similarity in %s",
            len(groups),
            path,
        )
        return groups

    def cleanup_duplicates(self, dry_run: bool = True) -> list[str]:
        """Remove duplicate files.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of removed/would-be-removed file paths
        """
        wiki_dir = self.wiki_root
        if not wiki_dir.exists():
            logger.warning("Директорію wiki не знайдено: %s", wiki_dir)
            return []

        # Find by suffix
        suffix_groups = self.find_duplicates_by_suffix(wiki_dir)
        removed = []

        for group in suffix_groups:
            base_file = wiki_dir / f"{group.base_slug}.md"
            if base_file.exists():
                # Delete all _N versions
                for dup in group.duplicates:
                    dup_file = wiki_dir / f"{dup}.md"
                    if dup_file.exists():
                        if not dry_run:
                            dup_file.unlink()
                            logger.info("Видалено дублікат: %s", dup_file)
                        removed.append(str(dup_file))
            else:
                # Keep highest _N, delete rest
                versions = [p for p in wiki_dir.glob(f"{group.base_slug}_*.md")]
                versions.sort(key=lambda p: int(re.search(r'_(\d+)$', p.stem).group(1)))
                if len(versions) > 1:
                    keep = versions[-1]
                    for v in versions[:-1]:
                        if not dry_run:
                            v.unlink()
                            logger.info("Видалено дублікат: %s", v)
                        removed.append(str(v))

                    # Rename highest to base
                    if keep.name != f"{group.base_slug}.md":
                        if not dry_run:
                            keep.rename(wiki_dir / f"{group.base_slug}.md")
                            logger.info("Перейменовано %s -> %s.md", keep, group.base_slug)
                        removed.append(str(keep))

        return removed
