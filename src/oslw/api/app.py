"""OSLW API Application — FastAPI entry point.

FastAPI application with:
- CORS middleware
- API v1 router
- Health endpoint
- OpenAPI docs at /docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oslw.api.v1.router import api_router
from oslw.config.settings import settings

app = FastAPI(
    title="OSLW API",
    description="Open Source Lightweight Wiki Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "wiki_root": str(settings.wiki_root),
        "wiki_exists": settings.wiki_root.exists(),
    }
