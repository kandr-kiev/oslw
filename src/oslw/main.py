"""OSLW FastAPI Application.

Entry point for the wiki management API server.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oslw.config.settings import settings
from oslw.config.logging import setup_logging, get_logger


# ============================================================================
# Application lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    setup_logging(settings)
    logger = get_logger("main")
    logger.info("OSLW starting on %s:%d", settings.api_host, settings.api_port)
    logger.info("Wiki root: %s", settings.wiki_root)
    logger.info("Database: %s", settings.database_url)
    
    # Verify wiki root exists
    if not settings.wiki_root.exists():
        logger.warning("Wiki root does not exist: %s", settings.wiki_root)
    
    yield
    
    # Shutdown
    logger.info("OSLW shutting down")


# ============================================================================
# Application factory
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="OSLW - Modular Wiki Management System",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register API routers (import here to avoid circular imports)
    from oslw.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
    
    # Health endpoint
    from fastapi import APIRouter
    health_router = APIRouter(tags=["health"])
    
    @health_router.get("/health", include_in_schema=False)
    async def health_check():
        return {
            "status": "ok",
            "version": settings.app_version,
            "wiki_root": str(settings.wiki_root),
            "wiki_exists": settings.wiki_root.exists(),
        }
    
    app.include_router(health_router)
    
    return app


# Create app instance for uvicorn
app = create_app()
