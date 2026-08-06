"""FastAPI routes for OSLW frontend.

Provides REST API endpoints for the wiki frontend:
- GET /api/pages - list all wiki pages
- GET /api/pages/{slug} - get specific page
- GET /api/stats - wiki statistics
- GET /api/search?q=... - search pages
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional

from oslw.infrastructure.database import FileManager, PageMeta
from oslw.config.settings import settings
from oslw.config.logging import get_logger

logger = get_logger("oslw.api.routes")

router = APIRouter(prefix="/api", tags=["api"])


def get_file_manager() -> FileManager:
    """Create FileManager instance from settings."""
    return FileManager(wiki_root=settings.wiki_root)


@router.get("/pages", summary="List all wiki pages")
async def list_pages(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Max pages to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List all wiki pages with optional category filter and pagination."""
    try:
        fm = get_file_manager()
        pages = fm.list_wiki_pages(category=category)
        
        # Apply pagination
        total = len(pages)
        pages = pages[offset:offset + limit]
        
        # Convert to serializable format
        page_list = []
        for page in pages:
            page_list.append({
                "slug": page.slug,
                "title": page.title,
                "type": page.type,
                "tags": page.tags,
                "created": page.created,
                "updated": page.updated,
            })
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "pages": page_list,
        }
    except Exception as e:
        logger.error("Error listing pages: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pages/{slug}", summary="Get specific page")
async def get_page(slug: str):
    """Get a specific wiki page by slug."""
    try:
        fm = get_file_manager()
        page = fm.read_page(slug)
        
        if not page:
            raise HTTPException(status_code=404, detail=f"Page not found: {slug}")
        
        return {
            "slug": page.slug,
            "title": page.title,
            "description": page.description,
            "type": page.type,
            "tags": page.tags,
            "sources": page.sources,
            "sha256": page.sha256,
            "created": page.created,
            "updated": page.updated,
            "content": page.content,
            "path": str(page.path),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error reading page %s: %s", slug, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Wiki statistics")
async def get_stats():
    """Get wiki statistics (page counts, types, tags)."""
    try:
        fm = get_file_manager()
        pages = fm.list_wiki_pages()
        
        # Count by type
        type_counts = {}
        for page in pages:
            type_counts[page.type] = type_counts.get(page.type, 0) + 1
        
        # Count by category (directory)
        category_counts = {}
        for page in pages:
            # Extract category from path
            rel_path = page.path.relative_to(fm.wiki_dir)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Collect all tags
        all_tags = set()
        for page in pages:
            all_tags.update(page.tags)
        
        return {
            "total_pages": len(pages),
            "types": type_counts,
            "categories": category_counts,
            "total_tags": len(all_tags),
            "tags": sorted(list(all_tags)),
        }
    except Exception as e:
        logger.error("Error getting stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="Search pages")
async def search_pages(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
):
    """Search wiki pages by title, slug, or content."""
    try:
        fm = get_file_manager()
        pages = fm.list_wiki_pages()
        
        query = q.lower()
        results = []
        
        for page in pages:
            # Search in title, slug, content, and tags
            searchable = f"{page.title} {page.slug} {page.content.lower()} {' '.join(page.tags).lower()}"
            
            if query in searchable:
                # Calculate relevance score
                score = 0
                if query in page.title.lower():
                    score += 10
                if query in page.slug.lower():
                    score += 8
                if query in page.content.lower():
                    score += 1
                if any(query in tag.lower() for tag in page.tags):
                    score += 5
                
                results.append({
                    "score": score,
                    "slug": page.slug,
                    "title": page.title,
                    "type": page.type,
                    "tags": page.tags,
                    "created": page.created,
                    "updated": page.updated,
                })
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "query": q,
            "total": len(results),
            "limit": limit,
            "results": results[:limit],
        }
    except Exception as e:
        logger.error("Error searching pages: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
