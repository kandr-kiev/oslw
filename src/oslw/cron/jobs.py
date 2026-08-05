"""OSLW Cron Jobs — scheduled task functions.

These functions are executed by the system cron (Hermes cron / systemd / crontab).
OSLW does NOT include an internal scheduler — scheduling is handled externally.

Available jobs:
- doctor_job: Run wiki integrity checks and repairs
- graph_job: Rebuild knowledge graph
- digest_job: Generate daily digest
- sources_job: Monitor content sources
- quality_job: Run linting and deduplication
- index_job: Rebuild index.md
"""

import logging
from pathlib import Path
from typing import Any

from oslw.config.settings import Settings
from oslw.application.quality_service import QualityService
from oslw.application.graph_service import GraphService
from oslw.application.digest_service import DigestService
from oslw.application.source_service import SourceService
from oslw.application.index_service import IndexService

logger = logging.getLogger(__name__)


def doctor_job(wiki_root: Path | str | None = None, **kwargs: Any) -> dict:
    """Run wiki integrity checks and repairs.

    Args:
        wiki_root: Path to wiki root directory.
        layers: Specific layer to check (comma-separated or "all").

    Returns:
        dict with status, issues count, and severity breakdown.
    """
    logger.info("doctor_job: Running wiki integrity checks")
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        quality = QualityService(wiki_root=s.wiki_root)
        result = quality.diagnose(layer=kwargs.get("layers", "all"))

        issues = result.issues if hasattr(result, 'issues') else []
        logger.info("doctor_job: Complete — %d issues found", len(issues))
        return {
            "status": "success",
            "total_issues": len(issues),
            "critical": sum(1 for i in issues if hasattr(i, 'severity') and i.severity == "critical"),
            "warning": sum(1 for i in issues if hasattr(i, 'severity') and i.severity == "warning"),
        }
    except Exception as e:
        logger.error("doctor_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}


def graph_job(wiki_root: Path | str | None = None, **kwargs: Any) -> dict:
    """Rebuild the knowledge graph.

    Args:
        wiki_root: Path to wiki root directory.

    Returns:
        dict with graph statistics and status.
    """
    logger.info("graph_job: Rebuilding knowledge graph")
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        graph_svc = GraphService(wiki_root=s.wiki_root)
        result = graph_svc.generate_graph()
        logger.info("graph_job: Complete — %d nodes, %d edges",
                    result.get('total_nodes', 0), result.get('total_edges', 0))
        return result
    except Exception as e:
        logger.error("graph_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}


def digest_job(wiki_root: Path | str | None = None, **kwargs: Any) -> str | dict:
    """Generate daily digest.

    Args:
        wiki_root: Path to wiki root directory.
        hours: Number of hours to look back (default 24).
        format: Output format (default "markdown").

    Returns:
        Digest content string or error dict.
    """
    hours = kwargs.get("hours", 24)
    fmt = kwargs.get("format", "markdown")
    logger.info("digest_job: Generating digest for last %dh", hours)
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        svc = DigestService(wiki_root=s.wiki_root)
        result = svc.generate_digest(hours=hours)
        summary = svc.get_digest_summary(hours=hours)
        return {
            "status": "success",
            "entries": len(result),
            "summary": summary.to_dict() if hasattr(summary, 'to_dict') else {
                "total_entries": summary.total_entries if hasattr(summary, 'total_entries') else 0,
                "by_type": summary.by_type if hasattr(summary, 'by_type') else {},
            },
        }
    except Exception as e:
        logger.error("digest_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}


def sources_job(wiki_root: Path | str | None = None, **kwargs: Any) -> dict:
    """Monitor content sources.

    Args:
        wiki_root: Path to wiki root directory.
        source_name: Specific source to check (optional).

    Returns:
        dict with monitoring results.
    """
    logger.info("sources_job: Checking content sources")
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        svc = SourceService(wiki_root=s.wiki_root)
        source_name = kwargs.get("source_name")
        result = svc.monitor_sources()
        logger.info("sources_job: Complete — %d sources checked", len(result))
        return {
            "status": "success",
            "results": result,
        }
    except Exception as e:
        logger.error("sources_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}


def quality_job(wiki_root: Path | str | None = None, **kwargs: Any) -> dict:
    """Run quality checks and deduplication.

    Args:
        wiki_root: Path to wiki root directory.

    Returns:
        dict with quality audit results.
    """
    logger.info("quality_job: Running quality checks")
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        svc = QualityService(wiki_root=s.wiki_root)
        report = svc.run_full_audit()
        logger.info("quality_job: Complete — %d issues found",
                    len(report.get("diagnosis", {}).get("issues", [])))
        return report
    except Exception as e:
        logger.error("quality_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}


def index_job(wiki_root: Path | str | None = None, **kwargs: Any) -> dict:
    """Rebuild the wiki index.

    Args:
        wiki_root: Path to wiki root directory.

    Returns:
        dict with index rebuild results.
    """
    logger.info("index_job: Rebuilding index")
    try:
        s = Settings(wiki_root=wiki_root) if wiki_root else Settings()
        svc = IndexService(wiki_root=s.wiki_root)
        count = svc.rebuild_index()
        logger.info("index_job: Complete — %d pages indexed", count)
        return {
            "status": "success",
            "total_pages": count,
        }
    except Exception as e:
        logger.error("index_job: Failed: %s", e)
        return {"status": "error", "error": str(e)}
