"""DatabaseManager - SQLAlchemy SQLite database management.

Provides:
- SQLite database connection
- Session management
- Model definitions

Usage:
    db = DatabaseManager(db_url="sqlite:///wiki.db")
    db.connect()
    session = db.get_session()
    try:
        # Use session
        pass
    finally:
        session.close()
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from oslw.config.logging import get_logger
from oslw.config.settings import Settings

logger = get_logger("infrastructure.database")


class DatabaseManager:
    """SQLite database manager for OSLW.

    Provides:
    - SQLite database connection with SQLAlchemy
    - Session management
    - Schema initialization

    Usage:
        db = DatabaseManager(wiki_root="/workspace/llm-wiki")
        db.connect()
        with db.get_session() as session:
            results = session.execute(text("SELECT * FROM pages"))
    """

    def __init__(self, settings: Optional[Settings] = None, db_url: Optional[str] = None):
        """Initialize DatabaseManager.

        Args:
            settings: Application settings
            db_url: Custom database URL
        """
        if db_url:
            self.db_url = db_url
        elif settings:
            db_path = Path(settings.data_dir) / "oslw.db"
            self.db_url = f"sqlite:///{db_path}"
        else:
            self.db_url = "sqlite:///oslw.db"

        self.engine = None
        self.SessionLocal = None

    def connect(self) -> None:
        """Initialize database connection.

        Creates engine and session factory.
        """
        # SQLite-specific settings
        connect_args = {}
        if self.db_url.startswith("sqlite://"):
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            self.db_url,
            connect_args=connect_args,
            echo=False,
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        # Initialize schema
        self._init_schema()

        logger.info("Database connected: %s", self.db_url)

    def _init_schema(self) -> None:
        """Initialize database schema.

        Creates tables if they don't exist.
        """
        with self.engine.connect() as conn:
            # Pages table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    type TEXT DEFAULT 'concept',
                    tags TEXT DEFAULT '[]',
                    sources TEXT DEFAULT '[]',
                    confidence REAL DEFAULT 0.5,
                    content TEXT,
                    sha256 TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Sources table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    interval_hours INTEGER DEFAULT 6,
                    last_checked TIMESTAMP,
                    last_error TEXT,
                    articles_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Graph nodes table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT UNIQUE NOT NULL,
                    label TEXT NOT NULL,
                    node_type TEXT DEFAULT 'wiki',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Graph edges table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    label TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, target)
                )
            """))

            conn.commit()
            logger.info("Database schema initialized")

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session.

        Yields:
            SQLAlchemy Session

        Example:
            with db.get_session() as session:
                results = session.execute(text("SELECT * FROM pages"))
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute(self, query: str, params: Optional[dict] = None):
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Query results
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def page_exists(self, slug: str) -> bool:
        """Check if a page exists in the database.

        Args:
            slug: Page slug

        Returns:
            True if page exists
        """
        with self.get_session() as session:
            result = session.execute(
                text("SELECT 1 FROM pages WHERE slug = :slug"),
                {"slug": slug},
            )
            return result.fetchone() is not None

    def upsert_page(self, slug: str, title: str, description: str = "",
                    page_type: str = "concept", tags: list = None,
                    content: str = "", sha256: str = "") -> None:
        """Insert or update a page in the database.

        Args:
            slug: Page slug
            title: Page title
            description: Page description
            page_type: Page type
            tags: List of tags
            content: Page content
            sha256: SHA256 hash
        """
        tags_json = json.dumps(tags or [])

        with self.get_session() as session:
            # Try to update
            session.execute(text("""
                UPDATE pages SET
                    title = :title,
                    description = :description,
                    type = :type,
                    tags = :tags,
                    content = :content,
                    sha256 = :sha256,
                    updated_at = CURRENT_TIMESTAMP
                WHERE slug = :slug
            """), {
                "slug": slug,
                "title": title,
                "description": description,
                "type": page_type,
                "tags": tags_json,
                "content": content,
                "sha256": sha256,
            })

            # If no rows updated, insert
            if session.execute(text("SELECT changes()")).fetchone()[0] == 0:
                session.execute(text("""
                    INSERT INTO pages (slug, title, description, type, tags, content, sha256)
                    VALUES (:slug, :title, :description, :type, :tags, :content, :sha256)
                """), {
                    "slug": slug,
                    "title": title,
                    "description": description,
                    "type": page_type,
                    "tags": tags_json,
                    "content": content,
                    "sha256": sha256,
                })

    def search_pages(self, query: str, limit: int = 10) -> list[dict]:
        """Search pages by title or description.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of page dictionaries
        """
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT slug, title, description, type, tags
                FROM pages
                WHERE title LIKE :query OR description LIKE :query
                LIMIT :limit
            """), {
                "query": f"%{query}%",
                "limit": limit,
            })

            return [
                {
                    "slug": row[0],
                    "title": row[1],
                    "description": row[2],
                    "type": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                }
                for row in result
            ]

    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
