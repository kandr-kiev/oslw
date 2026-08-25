"""Application settings - Pydantic Settings with env-based configuration."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # Application
    # ========================================================================
    app_name: str = "OSLW"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # ========================================================================
    # Wiki Root (source of truth - file-based ONLY, no database)
    # ========================================================================
    wiki_root: Path = Field(
        default=Path("/workspace/llm-wiki"),
        description="Root directory for wiki files (raw/ + wiki/). Override with OSLW_WIKI_ROOT env.",
    )

    # ========================================================================
    # API
    # ========================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
    )

    # ========================================================================
    # Authentication
    # ========================================================================
    api_key: str = Field(
        default="",
        description="API key for authentication. MUST be set via OSLW_API_KEY env.",
    )

    # ========================================================================
    # Frontend
    # ========================================================================
    frontend_url: str = "http://localhost:3000"

    # ========================================================================
    # Git
    # ========================================================================
    git_remote: str = "origin"
    git_branch: str = "main"

    # ========================================================================
    # Source Monitoring
    # ========================================================================
    monitor_interval_hours: int = 6
    monitor_timeout: int = 30  # seconds per request

    # ========================================================================
    # File Processing
    # ========================================================================
    max_file_size: int = 5 * 1024 * 1024  # 5 MB
    default_encoding: str = "utf-8"

    # ========================================================================
    # Graphify
    # ========================================================================
    graphify_output_dir: Path = Field(default=Path("graphify-out"))

    # ========================================================================
    # Logging
    # ========================================================================
    log_dir: Path = Field(default=Path("logs"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M"

    @property
    def raw_path(self) -> Path:
        """Path to raw articles directory."""
        return self.wiki_root / "raw"

    @property
    def wiki_path(self) -> Path:
        """Path to wiki pages directory."""
        return self.wiki_root

    @property
    def index_path(self) -> Path:
        """Path to wiki index.md."""
        return self.wiki_root / "index.md"

    @property
    def graph_file(self) -> Path:
        """Path to graph-from-wiki.json."""
        return self.wiki_root / "graph-from-wiki.json"

    @property
    def graphify_dir(self) -> Path:
        """Resolved graphify output directory."""
        return self.wiki_root / self.graphify_output_dir


# Singleton instance
settings = Settings()
