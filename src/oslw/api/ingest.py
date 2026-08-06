"""FastAPI routes for content ingestion.

Provides REST API endpoints for batch content ingestion:
- POST /api/ingest/batch - batch ingest articles
- GET /api/ingest/stats - ingestion statistics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from oslw.domain.sources.ingest import ContentIngestor
from oslw.config.settings import settings
from oslw.config.logging import get_logger

logger = get_logger("oslw.api.ingest")

router = APIRouter(prefix="/ingest", tags=["ingest"])


class ArticleInput(BaseModel):
    """Single article for ingestion."""
    title: str = Field(..., min_length=1, description="Article title")
    content: str = Field(..., min_length=1, description="Article content (markdown)")
    source_url: str = Field(default="", description="Original source URL")
    tags: list[str] = Field(default_factory=list, description="Article tags")
    source_name: str = Field(default="", description="Source name")


class BatchIngestRequest(BaseModel):
    """Batch ingestion request."""
    articles: list[ArticleInput] = Field(..., min_length=1, description="List of articles")


class BatchIngestResponse(BaseModel):
    """Batch ingestion response."""
    ingested: int
    skipped: int
    failed: int
    total: int
    details: list[dict]


@router.post("/batch", summary="Batch ingest articles", response_model=BatchIngestResponse)
async def batch_ingest(request: BatchIngestRequest):
    """Ingest multiple articles with deduplication.

    Skips articles whose slug already exists in raw/.
    Returns detailed per-article results.
    """
    try:
        ingestor = ContentIngestor(wiki_root=settings.wiki_root)
        articles = [a.model_dump() for a in request.articles]
        results = ingestor.ingest_all(articles)

        return BatchIngestResponse(**results)
    except Exception as e:
        logger.error("Error in batch ingest: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Ingestion statistics")
async def ingest_stats():
    """Get raw articles directory statistics."""
    try:
        raw_dir = settings.wiki_root / "raw" / "articles"
        if not raw_dir.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "files": [],
            }

        files = list(raw_dir.glob("*.md"))
        total_size = sum(f.stat().st_size for f in files)

        # Get top 10 largest files
        file_info = [
            {
                "filename": f.name,
                "size": f.stat().st_size,
            }
            for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:10]
        ]

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "top_files": file_info,
        }
    except Exception as e:
        logger.error("Error getting ingest stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
