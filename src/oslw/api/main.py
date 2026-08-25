"""OSLW FastAPI application.

Main entry point for the OSLW API server and frontend.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from oslw.config.settings import settings
from oslw.config.logging import get_logger
from oslw.api.routes import router
from oslw.api.graph import router as graph_router
from oslw.api.digest import router as digest_router
from oslw.api.ingest import router as ingest_router
from oslw.api.middleware import rate_limiter
from oslw.api.background import router as bg_router

logger = get_logger("oslw.api.main")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="OSLW - Modular Wiki Management System",
)

# Rate limiting middleware (100 req/min per client IP)
@app.middleware("http")
async def rate_limit_middleware(request: "Request", call_next):
    """Apply rate limiting to all API requests."""
    return await rate_limiter.middleware(request, call_next)

# Include API routes
app.include_router(router)
app.include_router(graph_router)
app.include_router(digest_router)
app.include_router(ingest_router)
app.include_router(bg_router)


# Serve frontend - look in multiple possible locations
def find_frontend_dir():
    """Find the frontend directory."""
    candidates = [
        Path(__file__).parent.parent.parent / "frontend",  # src/../frontend
        Path(__file__).parent.parent / "frontend",  # src/frontend
        Path(__file__).parent / "frontend",  # api/frontend
        Path("/workspace/projects/oslw/frontend"),  # absolute
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "index.html").exists():
            return candidate
    return None


FRONTEND_DIR = find_frontend_dir()


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page."""
    if FRONTEND_DIR:
        index_path = FRONTEND_DIR / "index.html"
        return FileResponse(index_path)
    return {"message": "Frontend not found"}


# Mount static files
if FRONTEND_DIR and FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "wiki_root": str(settings.wiki_root),
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("OSLW API запускається на %s:%d", settings.api_host, settings.api_port)
    logger.info("Корінь wiki: %s", settings.wiki_root)
    logger.info("Директорія frontend: %s", FRONTEND_DIR)
