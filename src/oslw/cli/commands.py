"""OSLW CLI - Typer-based command line interface.

Provides commands for wiki management:
- doctor: Diagnose and fix wiki issues
- sync: Synchronize raw → wiki
- graph: Generate knowledge graph
- digest: Generate daily digest
- monitor: Monitor sources
- status: Show wiki status
"""

from pathlib import Path

import typer

from oslw.config.settings import Settings, settings
from oslw.config.logging import setup_logging, get_logger

cli = typer.Typer(
    name="oslw",
    help="OSLW - Modular Wiki Management System",
    add_completion=True,
)


def _get_settings(path: Path | None) -> Settings:
    """Get settings, optionally overriding wiki_root."""
    if path:
        return Settings(wiki_root=path)
    return settings


@cli.command()
def status(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed information",
    ),
):
    """Show wiki status and health."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.status")

    logger.info("Wiki root: %s", s.wiki_root)
    logger.info("Exists: %s", s.wiki_root.exists())

    if not s.wiki_root.exists():
        typer.echo(f"❌ Wiki root does not exist: {s.wiki_root}")
        raise typer.Exit(1)

    # Count files
    wiki_count = sum(1 for _ in s.wiki_path.glob("**/*.md")) if s.wiki_path.exists() else 0
    raw_count = sum(1 for _ in s.raw_path.glob("**/*.md")) if s.raw_path.exists() else 0

    typer.echo(f"✅ Wiki root: {s.wiki_root}")
    typer.echo(f"   Wiki pages: {wiki_count}")
    typer.echo(f"   Raw articles: {raw_count}")

    if verbose:
        # Check index.md
        if s.index_path.exists():
            typer.echo(f"   Index.md: ✅ exists")
        else:
            typer.echo(f"   Index.md: ❌ missing")

        # Check schema
        if s.schema_path.exists():
            typer.echo(f"   Schema.md: ✅ exists")
        else:
            typer.echo(f"   Schema.md: ❌ missing")


@cli.command()
def doctor(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run",
        help="Don't apply fixes, just report",
    ),
    layer: str = typer.Option(
        None, "--layer", "-l",
        help="Specific layer to check (index, wiki_pages, metadata)",
    ),
):
    """Run WikiDoctor diagnosis."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.doctor")

    typer.echo(f"🔍 Running WikiDoctor diagnosis...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Dry run: {dry_run}")

    if layer:
        typer.echo(f"   Layer: {layer}")

    typer.echo(f"\n⚠️  Not implemented - domain layer in progress")
    typer.echo(f"   Phase 2: Domain layer implementation required")

    raise typer.Exit(0)


@cli.command()
def sync(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run",
        help="Don't apply changes, just report",
    ),
):
    """Synchronize raw articles to wiki pages."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.sync")

    typer.echo(f"🔄 Running sync...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Dry run: {dry_run}")

    typer.echo(f"\n⚠️  Not implemented - domain layer in progress")
    typer.echo(f"   Phase 2: Domain layer implementation required")

    raise typer.Exit(0)


@cli.command()
def graph(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    generate: bool = typer.Option(
        False, "--generate", "-g",
        help="Regenerate graph from wiki pages",
    ),
):
    """Manage knowledge graph."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.graph")

    if generate:
        typer.echo(f"📊 Generating graph...")
        typer.echo(f"   Wiki root: {s.wiki_root}")
        typer.echo(f"\n⚠️  Not implemented - domain layer in progress")
    else:
        typer.echo(f"📊 Graph status:")
        typer.echo(f"   Wiki root: {s.wiki_root}")

    raise typer.Exit(0)


@cli.command()
def digest(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    hours: int = typer.Option(
        24, "--hours", "-h",
        help="Hours to look back",
    ),
):
    """Generate daily digest."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.digest")

    typer.echo(f"📰 Generating digest...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Hours: {hours}")

    typer.echo(f"\n⚠️  Not implemented - domain layer in progress")
    typer.echo(f"   Phase 2: Domain layer implementation required")

    raise typer.Exit(0)


@cli.command()
def monitor(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    source: str = typer.Option(
        None, "--source", "-s",
        help="Specific source to check (rss, github, huggingface, youtube)",
    ),
):
    """Monitor sources for new content."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.monitor")

    typer.echo(f"📡 Checking sources...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    if source:
        typer.echo(f"   Source: {source}")

    typer.echo(f"\n⚠️  Not implemented - domain layer in progress")
    typer.echo(f"   Phase 2: Domain layer implementation required")

    raise typer.Exit(0)


if __name__ == "__main__":
    cli()
