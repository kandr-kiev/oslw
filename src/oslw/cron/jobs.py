"""OSLW Cron Jobs — specific scheduled tasks.

Cron jobs:
- DoctorJob: Run wiki integrity checks and repairs
- GraphJob: Rebuild knowledge graph
- DigestJob: Generate daily digest
- SourcesJob: Monitor content sources
- QualityJob: Run linting and deduplication
- IndexJob: Rebuild index.md
"""

import logging
from typing import Any

from oslw.application.quality_service import QualityService
from oslw.application.graph_service import GraphService
from oslw.application.digest_service import DigestService
from oslw.application.source_service import SourceService
from oslw.application.quality_service import QualityService
from oslw.application.index_service import IndexService
from oslw.config.settings import settings

logger = logging.getLogger(__name__)


class DoctorJob:
    """Wiki integrity check and repair job."""

    def __init__(self, quality_service: QualityService = None):
        self.service = quality_service or QualityService()

    def execute(self, **kwargs: Any) -> dict:
        """Run doctor checks and repairs."""
        logger.info("DoctorJob: Running wiki integrity checks")
        try:
            layers = kwargs.get("layers")
            result = self.service.diagnose(layer=layers or "all")
            # Return issues count and severity
            issues = result.issues if hasattr(result, 'issues') else []
            logger.info(f"DoctorJob: Complete — {len(issues)} issues found")
            return {
                "status": "success",
                "total_issues": len(issues),
                "critical": sum(1 for i in issues if hasattr(i, 'severity') and i.severity == "critical"),
                "warning": sum(1 for i in issues if hasattr(i, 'severity') and i.severity == "warning"),
            }
        except Exception as e:
            logger.error(f"DoctorJob: Failed: {e}")
            return {"status": "error", "error": str(e)}


class GraphJob:
    """Knowledge graph rebuild job."""

    def __init__(self, graph_service: GraphService = None):
        self.service = graph_service or GraphService()

    def execute(self, **kwargs: Any) -> dict:
        """Rebuild the knowledge graph."""
        logger.info("GraphJob: Rebuilding knowledge graph")
        try:
            result = self.service.generate_graph()
            logger.info(f"GraphJob: Complete — {result.get('total_nodes', 0)} nodes, {result.get('total_edges', 0)} edges")
            return result
        except Exception as e:
            logger.error(f"GraphJob: Failed: {e}")
            return {"status": "error", "error": str(e)}


class DigestJob:
    """Daily digest generation job."""

    def __init__(self, digest_service: DigestService = None):
        self.service = digest_service or DigestService()

    def execute(self, **kwargs: Any) -> str:
        """Generate daily digest."""
        hours = kwargs.get("hours", 24)
        fmt = kwargs.get("format", "markdown")
        logger.info(f"DigestJob: Generating digest for last {hours}h")
        try:
            result = self.service.generate_digest(hours=hours, format=fmt)
            logger.info("DigestJob: Complete")
            return result
        except Exception as e:
            logger.error(f"DigestJob: Failed: {e}")
            return f"Error: {e}"


class SourcesJob:
    """Content source monitoring job."""

    def __init__(self, source_service: SourceService = None):
        self.service = source_service or SourceService()

    def execute(self, **kwargs: Any) -> dict:
        """Monitor content sources."""
        logger.info("SourcesJob: Checking content sources")
        try:
            source_name = kwargs.get("source_name")
            result = self.service.check_sources(source_name=source_name)
            logger.info(f"SourcesJob: Complete — {len(result.get('results', []))} sources checked")
            return result
        except Exception as e:
            logger.error(f"SourcesJob: Failed: {e}")
            return {"status": "error", "error": str(e)}


class QualityJob:
    """Quality monitoring job."""

    def __init__(self, quality_service: QualityService = None):
        self.service = quality_service or QualityService()

    def execute(self, **kwargs: Any) -> dict:
        """Run quality checks."""
        logger.info("QualityJob: Running quality checks")
        try:
            result = self.service.run_quality_check()
            logger.info(f"QualityJob: Complete — {result.get('total_issues', 0)} issues found")
            return result
        except Exception as e:
            logger.error(f"QualityJob: Failed: {e}")
            return {"status": "error", "error": str(e)}


class IndexJob:
    """Index rebuild job."""

    def __init__(self, index_service: IndexService = None):
        self.service = index_service or IndexService()

    def execute(self, **kwargs: Any) -> dict:
        """Rebuild the wiki index."""
        logger.info("IndexJob: Rebuilding index")
        try:
            result = self.service.rebuild_index()
            logger.info(f"IndexJob: Complete — {result.get('total_pages', 0)} pages indexed")
            return result
        except Exception as e:
            logger.error(f"IndexJob: Failed: {e}")
            return {"status": "error", "error": str(e)}
