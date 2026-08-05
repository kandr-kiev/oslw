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

from oslw.cron.jobs import (
    doctor_job,
    graph_job,
    digest_job,
    sources_job,
    quality_job,
    index_job,
)

__all__ = [
    "doctor_job",
    "graph_job",
    "digest_job",
    "sources_job",
    "quality_job",
    "index_job",
]
