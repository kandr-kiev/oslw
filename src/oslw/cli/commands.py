"""OSLW CLI - Typer-based command line interface.

Provides commands for wiki management:
- doctor: Diagnose and fix wiki issues
- sync: Synchronize raw → wiki
- graph: Generate knowledge graph
- digest: Generate daily digest
- monitor: Monitor sources
- status: Show wiki status
- page: Manage wiki pages
"""

from pathlib import Path
from datetime import datetime, timezone
import json

import typer

from oslw.config.settings import Settings, settings
from oslw.config.logging import setup_logging, get_logger
from oslw.application import (
    PageService,
    IndexService,
    IntegrityService,
    GraphService,
    QualityService,
    DigestService,
    SourceService,
)

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


def _get_page_service(wiki_root: Path | None) -> PageService:
    """Get PageService instance."""
    s = _get_settings(wiki_root)
    return PageService(wiki_root=s.wiki_root)


def _get_quality_service(wiki_root: Path | None) -> QualityService:
    """Get QualityService instance."""
    s = _get_settings(wiki_root)
    return QualityService(wiki_root=s.wiki_root)


def _get_graph_service(wiki_root: Path | None) -> GraphService:
    """Get GraphService instance."""
    s = _get_settings(wiki_root)
    return GraphService(wiki_root=s.wiki_root)


def _get_digest_service(wiki_root: Path | None) -> DigestService:
    """Get DigestService instance."""
    s = _get_settings(wiki_root)
    return DigestService(wiki_root=s.wiki_root)


def _get_source_service(wiki_root: Path | None) -> SourceService:
    """Get SourceService instance."""
    s = _get_settings(wiki_root)
    return SourceService(wiki_root=s.wiki_root)


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
    apply: bool = typer.Option(
        False, "--apply",
        help="Apply fixes (only with --apply)",
    ),
):
    """Run WikiDoctor diagnosis and optionally fix issues."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.doctor")

    typer.echo(f"🔍 Running WikiDoctor diagnosis...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Dry run: {dry_run}")

    if layer:
        typer.echo(f"   Layer: {layer}")

    try:
        quality = _get_quality_service(wiki_root)

        # Run full audit
        audit = quality.run_full_audit()

        # Print diagnosis results
        diagnosis = audit["diagnosis"]
        typer.echo(f"\n📊 Diagnosis Results:")
        typer.echo(f"   Critical: {diagnosis['severity_counts'].get('critical', 0)}")
        typer.echo(f"   Warnings: {diagnosis['severity_counts'].get('warning', 0)}")
        typer.echo(f"   Info: {diagnosis['severity_counts'].get('info', 0)}")

        # Print quality stats
        quality_stats = audit["quality_stats"]
        typer.echo(f"\n📈 Quality Statistics:")
        typer.echo(f"   Total pages: {quality_stats['total_pages']}")
        typer.echo(f"   With frontmatter: {quality_stats['pages_with_frontmatter']}")
        typer.echo(f"   With SHA256: {quality_stats['pages_with_sha256']}")
        typer.echo(f"   Orphan pages: {quality_stats['orphan_pages']}")
        typer.echo(f"   Duplicate groups: {quality_stats['duplicate_groups']}")

        # Print issues
        if diagnosis["issues"]:
            typer.echo(f"\n⚠️  Issues Found:")
            for issue in diagnosis["issues"][:20]:  # Show first 20
                typer.echo(f"   - {issue}")
            if len(diagnosis["issues"]) > 20:
                typer.echo(f"   ... and {len(diagnosis['issues']) - 20} more")

        # Print validation errors
        if audit["validation_errors"]:
            typer.echo(f"\n🔍 Validation Errors:")
            for slug, errors in audit["validation_errors"].items():
                typer.echo(f"   {slug}:")
                for error in errors[:5]:
                    typer.echo(f"      - {error}")

        # Print duplicates
        if audit["duplicates"]:
            typer.echo(f"\n📦 Duplicate Groups: {len(audit['duplicates'])}")
            for i, group in enumerate(audit["duplicates"][:5]):
                typer.echo(f"   Group {i+1}: {', '.join(group[:3])}")

        # Apply fixes if requested
        if apply:
            typer.echo(f"\n🔧 Applying fixes...")
            removed = quality.cleanup_duplicates(dry_run=False)
            typer.echo(f"   Removed {len(removed)} duplicate files")

        typer.echo(f"\n✅ Diagnosis complete!")
        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error running doctor: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


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
    force: bool = typer.Option(
        False, "--force",
        help="Force sync even if files exist",
    ),
):
    """Synchronize raw articles to wiki pages."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.sync")

    typer.echo(f"🔄 Running sync...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Dry run: {dry_run}")

    try:
        source_service = _get_source_service(wiki_root)

        # List raw articles
        raw_articles = source_service.get_raw_articles()
        typer.echo(f"   Raw articles found: {len(raw_articles)}")

        if not raw_articles:
            typer.echo(f"   No raw articles to sync")
            raise typer.Exit(0)

        # Process each article
        synced = 0
        skipped = 0
        errors = 0

        for article_path in raw_articles:
            try:
                # Read article
                with open(article_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract title from content
                title = "Untitled"
                for line in content.splitlines()[:10]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # Check if page already exists
                slug = title.lower().replace(" ", "-").replace("—", "-")[:100]
                page_service = _get_page_service(wiki_root)

                if await page_service.page_exists(slug) and not force:
                    typer.echo(f"   ⏭️  Skip: {title}")
                    skipped += 1
                    continue

                # Create wiki page
                await page_service.create_page(
                    title=title,
                    content=content,
                    slug=slug,
                    page_type="concept",
                    tags=["synced"],
                )
                typer.echo(f"   ✅ Synced: {title}")
                synced += 1

            except Exception as e:
                logger.error("Error syncing %s: %s", article_path, str(e))
                typer.echo(f"   ❌ Error: {article_path} - {str(e)}")
                errors += 1

        typer.echo(f"\n📊 Sync Results:")
        typer.echo(f"   Synced: {synced}")
        typer.echo(f"   Skipped: {skipped}")
        typer.echo(f"   Errors: {errors}")

        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error running sync: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


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
    export: bool = typer.Option(
        False, "--export", "-e",
        help="Export graph to JSON file",
    ),
):
    """Manage knowledge graph."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.graph")

    try:
        graph_svc = _get_graph_service(wiki_root)

        if generate:
            typer.echo(f"📊 Generating graph...")
            typer.echo(f"   Wiki root: {s.wiki_root}")

            graph_dict = graph_svc.generate_graph()
            nodes = len(graph_dict.get("nodes", {}))
            edges = len(graph_dict.get("edges", []))

            typer.echo(f"   Generated: {nodes} nodes, {edges} edges")

            if export:
                output_path = graph_svc.export_graph()
                typer.echo(f"   Exported to: {output_path}")

        else:
            typer.echo(f"📊 Graph status:")
            typer.echo(f"   Wiki root: {s.wiki_root}")

            stats = graph_svc.get_stats()
            typer.echo(f"   Nodes: {stats.nodes}")
            typer.echo(f"   Edges: {stats.edges}")
            typer.echo(f"   Categories: {stats.categories}")
            typer.echo(f"   Density: {stats.density:.4f}")

        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error managing graph: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


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
    format: str = typer.Option(
        "markdown", "--format", "-f",
        help="Output format (markdown, json, text)",
    ),
    output: Path = typer.Option(
        None, "--output", "-o",
        help="Output file path",
    ),
):
    """Generate daily digest."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.digest")

    typer.echo(f"📰 Generating digest...")
    typer.echo(f"   Wiki root: {s.wiki_root}")
    typer.echo(f"   Hours: {hours}")
    typer.echo(f"   Format: {format}")

    try:
        digest_svc = _get_digest_service(wiki_root)

        # Generate digest
        content = await digest_svc.export_digest(hours=hours, format=format)

        # Output
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            typer.echo(f"   Exported to: {output}")
        else:
            typer.echo(f"\n{content}")

        # Print summary
        summary = await digest_svc.get_digest_summary(hours=hours)
        typer.echo(f"\n📊 Digest Summary:")
        typer.echo(f"   Total entries: {summary.total_entries}")
        typer.echo(f"   By type: {summary.by_type}")
        typer.echo(f"   By source: {summary.by_source}")

        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error generating digest: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


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

    try:
        source_svc = _get_source_service(wiki_root)

        # List sources
        stats = source_svc.list_sources()
        typer.echo(f"\n📋 Configured Sources:")
        for s in stats:
            status_icon = "✅" if not s.last_error else "❌"
            typer.echo(f"   {status_icon} {s.name} ({s.type}) - {s.articles_count} articles")

        # Check sources
        typer.echo(f"\n🔍 Checking sources...")
        results = source_svc.monitor_all()

        updated = 0
        for name, result in results.items():
            if result.get("updated"):
                typer.echo(f"   ✅ {name}: {result['updated']} new articles")
                updated += 1
            else:
                typer.echo(f"   ⏭️  {name}: no updates")

        typer.echo(f"\n📊 Monitor Results:")
        typer.echo(f"   Sources checked: {len(results)}")
        typer.echo(f"   Sources updated: {updated}")

        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error monitoring sources: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


@cli.command()
def page(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    slug: str = typer.Option(
        None, "--slug", "-s",
        help="Page slug",
    ),
    list: bool = typer.Option(
        False, "--list", "-l",
        help="List all pages",
    ),
    count: bool = typer.Option(
        False, "--count", "-c",
        help="Show page count",
    ),
):
    """Manage wiki pages."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.page")

    try:
        page_svc = _get_page_service(wiki_root)

        if list:
            # List pages
            result = await page_svc.list_pages(limit=50, offset=0)
            typer.echo(f"📄 Wiki Pages ({result.total} total):")
            for p in result.pages:
                typer.echo(f"   - {p.slug}: {p.title} ({p.type})")

        elif count:
            # Show count
            total = await page_svc.get_page_count()
            typer.echo(f"📄 Total pages: {total}")

        elif slug:
            # Get single page
            try:
                page = await page_svc.get_page(slug)
                typer.echo(f"📄 Page: {page.title}")
                typer.echo(f"   Slug: {page.slug}")
                typer.echo(f"   Type: {page.type}")
                typer.echo(f"   Tags: {', '.join(page.tags)}")
                typer.echo(f"   Created: {page.created}")
                typer.echo(f"   Updated: {page.updated}")
                typer.echo(f"   Word count: {page.word_count}")
                typer.echo(f"   Line count: {page.line_count}")
            except Exception as e:
                typer.echo(f"❌ Error: {str(e)}")
                raise typer.Exit(1)

        else:
            typer.echo(f"❌ Provide --list, --count, or --slug")
            raise typer.Exit(1)

        raise typer.Exit(0)

    except Exception as e:
        logger.error("Error managing pages: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


@cli.command()
def cron(
    wiki_root: Path = typer.Option(
        None, "--wiki-root", "-r",
        help="Path to wiki root directory",
    ),
    list: bool = typer.Option(
        False, "--list", "-l",
        help="List all cron jobs",
    ),
    run: str = typer.Option(
        None, "--run", "-r",
        help="Run a specific cron job (doctor, graph, digest, sources, quality, index)",
    ),
    run_all: bool = typer.Option(
        False, "--run-all",
        help="Run all enabled cron jobs",
    ),
):
    """Manage cron jobs."""
    s = _get_settings(wiki_root)
    setup_logging(s)
    logger = get_logger("cli.cron")

    try:
        from oslw.cron.scheduler import CronScheduler
        from oslw.cron.jobs import (
            DoctorJob,
            GraphJob,
            DigestJob,
            SourcesJob,
            QualityJob,
            IndexJob,
        )

        scheduler = CronScheduler()

        # Register jobs
        scheduler.register(
            "doctor",
            DoctorService(wiki_root=s.wiki_root).diagnose,
            interval=3600,
            enabled=True,
            fix_sha256=True,
            fix_wikilinks=True,
        )
        scheduler.register(
            "graph",
            GraphService(wiki_root=s.wiki_root).generate_graph,
            interval=7200,
            enabled=True,
        )
        scheduler.register(
            "digest",
            DigestService(wiki_root=s.wiki_root).generate_digest,
            interval=86400,
            enabled=True,
            hours=24,
            format="markdown",
        )
        scheduler.register(
            "sources",
            SourceService(wiki_root=s.wiki_root).check_sources,
            interval=3600,
            enabled=True,
        )
        scheduler.register(
            "quality",
            QualityService(wiki_root=s.wiki_root).run_quality_check,
            interval=14400,
            enabled=True,
        )
        scheduler.register(
            "index",
            IndexService(wiki_root=s.wiki_root).rebuild_index,
            interval=1800,
            enabled=True,
        )

        if list:
            typer.echo(f"📋 Cron Jobs:")
            for job in scheduler.list_jobs():
                status = "✅" if job["enabled"] else "❌"
                typer.echo(f"   {status} {job['name']} (every {job['interval']}s)")
                if job["last_run"]:
                    typer.echo(f"      Last run: {job['last_run']}")
                if job["last_error"]:
                    typer.echo(f"      Error: {job['last_error']}")
            raise typer.Exit(0)

        if run:
            typer.echo(f"▶️  Running job: {run}")
            result = await scheduler.run_job(run)
            typer.echo(f"   Status: {result.get('status')}")
            if result.get("error"):
                typer.echo(f"   Error: {result['error']}")
            if result.get("result"):
                if isinstance(result["result"], dict):
                    for key, value in result["result"].items():
                        typer.echo(f"   {key}: {value}")
            raise typer.Exit(0)

        if run_all:
            typer.echo(f"▶️  Running all jobs...")
            results = await scheduler.run_all()
            typer.echo(f"\n📊 Results:")
            for result in results:
                status_icon = "✅" if result.get("status") == "success" else "❌"
                typer.echo(f"   {status_icon} {result['name']}: {result.get('status')}")
            raise typer.Exit(0)

        typer.echo(f"❌ Provide --list, --run, or --run-all")
        raise typer.Exit(1)

    except Exception as e:
        logger.error("Error managing cron: %s", str(e))
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
