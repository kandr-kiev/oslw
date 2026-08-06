"""FastAPI routes for digest generation operations.

Provides REST API endpoints for digest management:
- GET /api/digest - generate and return digest
- POST /api/digest/save - save digest to disk
- GET /api/digest/recent - recent entries
- GET /api/digest/list - list saved digests
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Optional

from oslw.application import DigestService
from oslw.config.settings import settings
from oslw.config.logging import get_logger

logger = get_logger("oslw.api.digest")

router = APIRouter(prefix="/digest", tags=["digest"])


def get_digest_service() -> DigestService:
    """Create DigestService instance from settings."""
    return DigestService(wiki_root=settings.wiki_root)


@router.get("", summary="Generate digest")
async def get_digest(
    hours: int = 24,
    format: str = "markdown",
):
    """Generate a digest for the specified time period.

    Args:
        hours: Number of hours to look back
        format: Output format (markdown, json, text)
    """
    try:
        svc = get_digest_service()
        content = svc.export_digest(hours=hours, format=format)
        summary = svc.get_digest_summary(hours=hours)

        return {
            "hours_covered": hours,
            "format": format,
            "total_entries": summary.total_entries,
            "by_type": summary.by_type,
            "by_source": summary.by_source,
            "content": content,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error generating digest: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", summary="Save digest to disk")
async def save_digest(
    hours: int = 24,
    format: str = "markdown",
    output_dir: Optional[str] = None,
):
    """Generate, export, and save digest to disk.

    Args:
        hours: Number of hours to look back
        format: Output format (markdown, json, text)
        output_dir: Custom output directory
    """
    try:
        svc = get_digest_service()
        path = svc.save_digest(hours=hours, format=format, output_dir=output_dir)

        return {
            "path": str(path),
            "size": path.stat().st_size,
        }
    except Exception as e:
        logger.error("Error saving digest: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", summary="Recent digest entries")
async def recent_entries(
    limit: int = 10,
    hours: int = 24,
):
    """Get most recent digest entries.

    Args:
        limit: Maximum number of entries
        hours: Number of hours to look back
    """
    try:
        svc = get_digest_service()
        entries = svc.get_recent_entries(limit=limit, hours=hours)
        return {
            "limit": limit,
            "hours_covered": hours,
            "total": len(entries),
            "entries": [e.to_dict() for e in entries],
        }
    except Exception as e:
        logger.error("Error getting recent entries: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", summary="List saved digests")
async def list_saved_digests(
    output_dir: Optional[str] = None,
):
    """List all saved digest files.

    Args:
        output_dir: Custom output directory
    """
    try:
        svc = get_digest_service()
        digests = svc.list_saved_digests(output_dir=output_dir)
        return {
            "digests": digests,
            "total": len(digests),
        }
    except Exception as e:
        logger.error("Error listing digests: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
