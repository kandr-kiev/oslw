"""Content scanners - fetch and parse content from external sources.

Provides:
- RSSScanner: Parse RSS/Atom feeds via feedparser
- GitHubScanner: Monitor GitHub repos for releases/issues
- HuggingFaceScanner: Monitor HF for new models/datasets
- YouTubeScanner: Monitor YouTube channels for new videos

Usage:
    from oslw.domain.sources.scanners import RSSScanner
    scanner = RSSScanner()
    articles = scanner.fetch(url="https://example.com/feed.xml", limit=10)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oslw.config.logging import get_logger
from oslw.utils.slug import norm_name

logger = get_logger("domain.sources.scanners")


@dataclass
class RawArticle:
    """A raw article fetched from a source.

    Attributes:
        title: Article title
        slug: URL-friendly slug
        content: Markdown content body
        url: Original source URL
        published: Publication timestamp
        author: Author name (if available)
        summary: Brief summary/description
        tags: Associated tags
        source_name: Source identifier
        content_hash: SHA256 of content (for dedup)
    """

    title: str
    slug: str
    content: str
    url: str
    published: Optional[datetime] = None
    author: Optional[str] = None
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    source_name: str = ""
    content_hash: str = ""

    def __post_init__(self):
        """Generate content_hash after init."""
        if not self.content_hash:
            raw = f"{self.title}{self.content}{self.url}".encode("utf-8")
            self.content_hash = hashlib.sha256(raw).hexdigest()[:16]


class RSSScanner:
    """Scan RSS/Atom feeds for new articles.

    Uses feedparser to parse RSS 2.0, Atom, and other feed formats.
    Extracts title, link, summary, published date, and author.

    Usage:
        scanner = RSSScanner()
        articles = scanner.fetch(
            url="https://feeds.bbci.co.uk/news/technology/rss.xml",
            source_name="bbc-news",
            tags=["news", "technology"]
        )
    """

    MAX_TITLE_LENGTH = 200
    MAX_SUMMARY_LENGTH = 5000

    def fetch(
        self,
        url: str,
        source_name: str = "",
        tags: Optional[list[str]] = None,
        limit: int = 20,
        timeout: int = 30,
    ) -> list[RawArticle]:
        """Fetch articles from an RSS feed.

        Args:
            url: RSS feed URL
            source_name: Source identifier for tracking
            tags: Default tags for all articles
            limit: Maximum articles to return
            timeout: Request timeout in seconds

        Returns:
            List of RawArticle objects
        """
        tags = tags or []
        articles = []

        try:
            import feedparser

            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                logger.warning("Feed parsing error for %s: %s", url, feed.bozo_exception)
                return []

            for entry in feed.entries[:limit]:
                article = self._parse_entry(entry, source_name, tags)
                if article:
                    articles.append(article)

            logger.info(
                "RSSScanner: отримано %d статей з %s (%d у стрічці)",
                len(articles),
                source_name or url,
                len(feed.entries),
            )

        except ImportError:
            logger.error("feedparser не встановлено. Встановіть: pip install feedparser")
        except Exception as e:
            logger.error("RSSScanner не вдалося для %s: %s", url, e)

        return articles

    def _parse_entry(
        self,
        entry: dict,
        source_name: str,
        tags: list[str],
    ) -> Optional[RawArticle]:
        """Parse a single RSS feed entry into a RawArticle.

        Args:
            entry: feedparser entry dict
            source_name: Source identifier
            tags: Default tags

        Returns:
            RawArticle or None if invalid
        """
        title = self._clean_text(entry.get("title", ""))
        if not title:
            return None

        url = self._get_url(entry)
        summary = self._clean_text(entry.get("summary", "") or entry.get("description", ""))
        published = self._parse_published(entry.get("published", ""))
        author = self._clean_text(entry.get("author", ""))

        # Build markdown content
        content = self._build_content(title, summary, url, published, author)
        slug = self._generate_slug(title)

        return RawArticle(
            title=title,
            slug=slug,
            content=content,
            url=url,
            published=published,
            author=author,
            summary=summary[:self.MAX_SUMMARY_LENGTH],
            tags=tags,
            source_name=source_name,
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Raw text from feed

        Returns:
            Cleaned text
        """
        if not text:
            return ""
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Truncate
        if len(text) > self.MAX_TITLE_LENGTH:
            text = text[: self.MAX_TITLE_LENGTH - 3] + "..."
        return text

    def _get_url(self, entry: dict) -> str:
        """Extract URL from feed entry.

        Args:
            entry: feedparser entry dict

        Returns:
            URL string
        """
        # Try standard link fields
        for key in ("link", "id", "guid"):
            if entry.get(key):
                return entry[key]
        # Try links array
        links = entry.get("links", [])
        if links:
            return links[0].get("href", links[0]) if isinstance(links[0], dict) else str(links[0])
        return ""

    def _parse_published(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date string to datetime.

        Args:
            date_str: Date string from feed

        Returns:
            datetime or None
        """
        if not date_str:
            return None
        try:
            import time
            import calendar

            parsed = time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
        except (ValueError, TypeError):
            pass
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _build_content(
        self,
        title: str,
        summary: str,
        url: str,
        published: Optional[datetime],
        author: Optional[str],
    ) -> str:
        """Build markdown content from article data.

        Args:
            title: Article title
            summary: Article summary
            url: Source URL
            published: Publication date
            author: Author name

        Returns:
            Markdown content string
        """
        lines = [f"# {title}", ""]

        if published:
            lines.append(f"**Published:** {published.strftime('%Y-%m-%d %H:%M UTC')}")
        if author:
            lines.append(f"**Author:** {author}")
        if url:
            lines.append(f"**Source:** [{url}]({url})")

        lines.append("")

        if summary:
            lines.append(summary)
        else:
            lines.append("*No summary available. [Read original article]({})*".format(url))

        lines.append("")
        lines.append("---")
        lines.append(f"*Collected by RSS scanner at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(lines)

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title.

        Args:
            title: Article title

        Returns:
            URL-friendly slug
        """
        slug = norm_name(title)
        if len(slug) < 3:
            slug = f"rss-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return slug


class GitHubScanner:
    """Monitor GitHub repositories for updates.

    Watches for new releases, issues, and PRs.
    Uses GitHub API (no auth for public repos).

    Usage:
        scanner = GitHubScanner()
        articles = scanner.fetch(
            repo="openai/openai-python",
            source_name="openai-changelog",
            tags=["openai", "api"]
        )
    """

    API_BASE = "https://api.github.com"

    def fetch(
        self,
        repo: str,
        source_name: str = "",
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[RawArticle]:
        """Fetch updates from a GitHub repo.

        Args:
            repo: GitHub repo in format "owner/repo"
            source_name: Source identifier
            tags: Default tags
            limit: Maximum updates to return

        Returns:
            List of RawArticle objects
        """
        tags = tags or []
        articles = []

        try:
            import json

            # Fetch releases
            releases_url = f"{self.API_BASE}/repos/{repo}/releases?per_page={limit}"
            releases = self._fetch_json(releases_url)

            if releases:
                for release in releases[:limit]:
                    article = self._parse_release(release, repo, source_name, tags)
                    if article:
                        articles.append(article)

            logger.info(
                "GitHubScanner: отримано %d релізів з %s",
                len(articles),
                repo,
            )

        except Exception as e:
            logger.error("GitHubScanner не вдалося для %s: %s", repo, e)

        return articles

    def _parse_release(
        self,
        release: dict,
        repo: str,
        source_name: str,
        tags: list[str],
    ) -> Optional[RawArticle]:
        """Parse a GitHub release into a RawArticle.

        Args:
            release: GitHub release dict
            repo: Repository name
            source_name: Source identifier
            tags: Default tags

        Returns:
            RawArticle or None
        """
        title = release.get("name") or release.get("tag_name")
        if not title:
            return None

        body = release.get("body", "") or ""
        url = release.get("html_url", "")
        published = None
        if release.get("published_at"):
            try:
                published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        content = f"# {title}\n\n"
        content += f"**Repository:** `{repo}`\n\n"
        if published:
            content += f"**Published:** {published.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        content += f"**Source:** [{url}]({url})\n\n"
        if body:
            content += body
        else:
            content += "*No release notes available.*"

        slug = self._generate_slug(title)

        return RawArticle(
            title=title,
            slug=slug,
            content=content,
            url=url,
            published=published,
            summary=body[:500] if body else "",
            tags=tags + ["github", "release"],
            source_name=source_name,
        )

    def _fetch_json(self, url: str) -> Optional[list]:
        """Fetch JSON from a URL.

        Args:
            url: URL to fetch

        Returns:
            Parsed JSON list or None
        """
        try:
            import requests

            resp = requests.get(url, timeout=30, headers={"Accept": "application/vnd.github.v3+json"})
            if resp.status_code == 200:
                return resp.json()
            logger.warning("GitHub API %s: status %d", url, resp.status_code)
            return None
        except Exception as e:
            logger.error("GitHub API fetch failed for %s: %s", url, e)
            return None

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug."""
        slug = norm_name(title)
        if len(slug) < 3:
            slug = f"gh-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return slug


class HuggingFaceScanner:
    """Monitor Hugging Face for new models and datasets.

    Uses the HF API to fetch trending/new models.

    Usage:
        scanner = HuggingFaceScanner()
        articles = scanner.fetch(
            source_name="huggingface-new-models",
            tags=["huggingface", "models"]
        )
    """

    API_BASE = "https://huggingface.co/api"

    def fetch(
        self,
        source_name: str = "",
        tags: Optional[list[str]] = None,
        limit: int = 10,
        model_type: str = "models",
    ) -> list[RawArticle]:
        """Fetch trending models/datasets from Hugging Face.

        Args:
            source_name: Source identifier
            tags: Default tags
            limit: Maximum items to return
            model_type: "models" or "datasets"

        Returns:
            List of RawArticle objects
        """
        tags = tags or []
        articles = []

        try:
            import requests

            endpoint = f"{self.API_BASE}/{model_type}"
            params = {"sort": "downloads", "limit": limit}

            resp = requests.get(endpoint, params=params, timeout=30)
            if resp.status_code != 200:
                logger.error("HF API помилка: %d", resp.status_code)
                return []

            items = resp.json()

            for item in items[:limit]:
                article = self._parse_item(item, source_name, tags, model_type)
                if article:
                    articles.append(article)

            logger.info(
                "HuggingFaceScanner: отримано %d %s з HF",
                len(articles),
                model_type,
            )

        except Exception as e:
            logger.error("HuggingFaceScanner не вдалося: %s", e)

        return articles

    def _parse_item(
        self,
        item: dict,
        source_name: str,
        tags: list[str],
        model_type: str,
    ) -> Optional[RawArticle]:
        """Parse a HF model/dataset into a RawArticle.

        Args:
            item: HF API item dict
            source_name: Source identifier
            tags: Default tags
            model_type: "models" or "datasets"

        Returns:
            RawArticle or None
        """
        id_str = item.get("id", "")
        if not id_str:
            return None

        title = item.get("modelId") or item.get("id") or id_str
        url = f"https://huggingface.co/{id_str}"

        # Build content
        content = f"# {title}\n\n"
        content += f"**Type:** {model_type}\n\n"
        content += f"**Source:** [{url}]({url})\n\n"

        # Add metadata
        if item.get("downloads") is not None:
            content += f"**Downloads:** {item['downloads']:,}\n\n"
        if item.get("likes") is not None:
            content += f"**Likes:** {item['likes']}\n\n"
        if item.get("tags"):
            content += f"**Tags:** {', '.join(item['tags'])}\n\n"

        # Add description if available
        if item.get("cardData", {}).get("dataset_summary"):
            content += f"\n{item['cardData']['dataset_summary']}\n"
        elif item.get("pipeline_tag"):
            content += f"\n**Pipeline:** {item['pipeline_tag']}\n"

        slug = self._generate_slug(title)

        return RawArticle(
            title=title,
            slug=slug,
            content=content,
            url=url,
            summary=id_str,
            tags=tags + [model_type, "huggingface"],
            source_name=source_name,
        )

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug.

        Keeps the ``/`` separator so org/model ids (e.g. ``test-org/test-model``)
        survive as ``test-org/test-model``.
        """
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\-./\u0400-\u04ff]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if len(slug) < 3:
            slug = f"hf-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return slug


class YouTubeScanner:
    """Monitor YouTube channels for new videos.

    Uses YouTube Data API or RSS feeds for video discovery.

    Usage:
        scanner = YouTubeScanner()
        articles = scanner.fetch(
            channel_id="UC29ju8bIPH5as8OGn4zwJ8A",
            source_name="youtube-ai-channels",
            tags=["youtube", "ai"]
        )
    """

    def fetch(
        self,
        channel_id: str = "",
        channel_url: str = "",
        source_name: str = "",
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[RawArticle]:
        """Fetch recent videos from a YouTube channel.

        Args:
            channel_id: YouTube channel ID
            channel_url: YouTube channel URL (alternative)
            source_name: Source identifier
            tags: Default tags
            limit: Maximum videos to return

        Returns:
            List of RawArticle objects
        """
        tags = tags or []
        articles = []

        # Try RSS feed approach (works for most channels)
        if channel_url:
            # Extract channel ID from URL if needed
            import re
            match = re.search(r"channel/(UC\w+)", channel_url)
            if match:
                channel_id = match.group(1)

        if channel_id:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            articles = self._fetch_rss(rss_url, source_name, tags, limit)

        if not articles and channel_url:
            # Fallback: try extracting from channel URL directly
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            articles = self._fetch_rss(rss_url, source_name, tags, limit)

        logger.info(
            "YouTubeScanner: fetched %d videos from %s",
            len(articles),
            source_name or channel_id,
        )

        return articles

    def _fetch_rss(
        self,
        rss_url: str,
        source_name: str,
        tags: list[str],
        limit: int,
    ) -> list[RawArticle]:
        """Fetch videos from YouTube RSS feed.

        Args:
            rss_url: YouTube RSS feed URL
            source_name: Source identifier
            tags: Default tags
            limit: Maximum videos

        Returns:
            List of RawArticle objects
        """
        articles = []

        try:
            import feedparser

            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:limit]:
                video_id = ""
                link = entry.get("link", "")
                # Extract video ID from URL
                match = re.search(r"v=([a-zA-Z0-9_-]+)", link)
                if match:
                    video_id = match.group(1)

                title = self._clean_text(entry.get("title", ""))
                if not title:
                    continue

                published = self._parse_published(entry.get("published", ""))
                author = entry.get("author", "")

                content = f"# {title}\n\n"
                content += f"**Published:** {published.strftime('%Y-%m-%d %H:%M UTC') if published else 'Unknown'}\n\n"
                content += f"**Author:** {author}\n\n"
                content += f"**Video:** [{link}]({link})\n\n"

                if entry.get("summary"):
                    content += f"\n{self._clean_text(entry['summary'])}\n"

                slug = self._generate_slug(title, video_id)

                articles.append(RawArticle(
                    title=title,
                    slug=slug,
                    content=content,
                    url=link,
                    published=published,
                    author=author,
                    summary=self._clean_text(entry.get("summary", ""))[:200],
                    tags=tags + ["youtube", "video"],
                    source_name=source_name,
                ))

        except Exception as e:
            logger.error("YouTubeScanner RSS fetch failed for %s: %s", rss_url, e)

        return articles

    def _clean_text(self, text: str) -> str:
        """Clean text from YouTube feed."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", text).strip()[:500]

    def _parse_published(self, date_str: str) -> Optional[datetime]:
        """Parse YouTube RSS date."""
        if not date_str:
            return None
        try:
            import time
            import calendar
            parsed = time.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
        except (ValueError, TypeError):
            pass
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None

    def _generate_slug(self, title: str, video_id: str = "") -> str:
        """Generate slug with video ID for uniqueness."""
        slug = norm_name(title)
        if video_id and len(slug) < 10:
            slug = f"yt-{video_id}"
        elif len(slug) < 3:
            slug = f"yt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return slug
