"""Wiki page endpoints — CRUD operations for wiki pages.

Uses PageService from Application Layer for all operations.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from oslw.api.v1.schemas import (
    WikiPageCreate,
    WikiPageUpdate,
    WikiPageResponse,
)
from oslw.api.deps import get_settings, get_api_key
from oslw.config.settings import Settings
from oslw.application import PageService
from oslw.core.exceptions import PageNotFoundError, ValidationError
from oslw.config.logging import get_logger

router = APIRouter(tags=["wiki"])
logger = get_logger("api.wiki")


def get_page_service(settings: Settings = Depends(get_settings)) -> PageService:
    """Dependency injection for PageService."""
    return PageService(wiki_root=settings.wiki_root)


@router.get(
    "/",
    response_model=list[WikiPageResponse],
    summary="List wiki pages",
    description="Get all wiki pages with optional filters",
)
def list_pages(
    category: Optional[str] = Query(None, description="Filter by page type"),
    type_filter: Optional[str] = Query(None, description="Filter by page type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    page_service: PageService = Depends(get_page_service),
) -> list[WikiPageResponse]:
    """List wiki pages with pagination and filters."""
    try:
        result = page_service.list_pages(
            category=category,
            type_filter=type_filter,
            tag=tag,
            limit=limit,
            offset=offset,
        )

        return [
            WikiPageResponse(
                slug=p.slug,
                title=p.title,
                description=p.description,
                type=p.type,
                tags=p.tags,
                sources=p.sources,
                created=p.created,
                updated=p.updated,
                content=p.content,
                word_count=p.word_count,
                line_count=p.line_count,
            )
            for p in result.pages
        ]
    except Exception as e:
        logger.error("Помилка списку сторінок: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{slug}",
    response_model=WikiPageResponse,
    summary="Get wiki page",
    description="Get a single wiki page by slug",
)
def get_page(
    slug: str,
    page_service: PageService = Depends(get_page_service),
) -> WikiPageResponse:
    """Get a wiki page by its slug."""
    try:
        page = page_service.get_page(slug)
        return WikiPageResponse(
            slug=page.slug,
            title=page.title,
            description=page.description,
            type=page.type,
            tags=page.tags,
            sources=page.sources,
            created=page.created,
            updated=page.updated,
            content=page.content,
            word_count=page.word_count,
            line_count=page.line_count,
        )
    except PageNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Wiki page not found: {slug}",
        )
    except Exception as e:
        logger.error("Помилка отримання сторінки %s: %s", slug, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/",
    response_model=WikiPageResponse,
    status_code=201,
    summary="Create wiki page",
    description="Create a new wiki page",
)
def create_page(
    page_data: WikiPageCreate,
    page_service: PageService = Depends(get_page_service),
    api_key: str = Depends(get_api_key),
) -> WikiPageResponse:
    """Create a new wiki page."""
    try:
        created = page_service.create_page(
            title=page_data.title,
            content=page_data.content,
            slug=page_data.slug,
            page_type=page_data.type,
            tags=page_data.tags,
            sources=page_data.sources,
        )

        return WikiPageResponse(
            slug=created.slug,
            title=created.title,
            description=created.description,
            type=created.type,
            tags=created.tags,
            sources=created.sources,
            created=created.created,
            updated=created.updated,
            content=created.content,
            word_count=created.word_count,
            line_count=created.line_count,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        logger.error("Помилка створення сторінки: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{slug}",
    response_model=WikiPageResponse,
    summary="Update wiki page",
    description="Update an existing wiki page",
)
def update_page(
    slug: str,
    page_data: WikiPageUpdate,
    page_service: PageService = Depends(get_page_service),
    api_key: str = Depends(get_api_key),
) -> WikiPageResponse:
    """Update an existing wiki page."""
    try:
        updated = page_service.update_page(
            slug=slug,
            title=page_data.title,
            content=page_data.content,
            tags=page_data.tags,
        )

        return WikiPageResponse(
            slug=updated.slug,
            title=updated.title,
            description=updated.description,
            type=updated.type,
            tags=updated.tags,
            sources=updated.sources,
            created=updated.created,
            updated=updated.updated,
            content=updated.content,
            word_count=updated.word_count,
            line_count=updated.line_count,
        )
    except PageNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Wiki page not found: {slug}",
        )
    except Exception as e:
        logger.error("Помилка оновлення сторінки %s: %s", slug, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{slug}",
    status_code=204,
    summary="Delete wiki page",
    description="Delete a wiki page by slug",
)
def delete_page(
    slug: str,
    page_service: PageService = Depends(get_page_service),
    api_key: str = Depends(get_api_key),
) -> None:
    """Delete a wiki page."""
    try:
        page_service.delete_page(slug)
    except PageNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Wiki page not found: {slug}",
        )
    except Exception as e:
        logger.error("Помилка видалення сторінки %s: %s", slug, str(e))
        raise HTTPException(status_code=500, detail=str(e))
