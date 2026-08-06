"""OSLW API Application — FastAPI entry point.

FastAPI application with:
- CORS middleware
- API v1 router
- Health endpoint
- OpenAPI docs at /docs (auth-protected)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_403_FORBIDDEN

from oslw.api.v1.router import api_router
from oslw.config.settings import settings, Settings
from functools import lru_cache


@lru_cache()
def get_settings() -> Settings:
    return settings


app = FastAPI(
    title="OSLW API",
    description="Open Source Lightweight Wiki Management System",
    version="0.1.0",
    docs_url=None,  # Disabled by default
    redoc_url=None,  # Disabled by default
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(api_router, prefix="/api/v1")


# Auth-protected docs endpoints
@app.get("/docs", include_in_schema=False)
async def docs_endpoint(request: Request):
    """OpenAPI docs — requires valid API key."""
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key or api_key != get_settings().api_key:
        return RedirectResponse(url="/redoc")
    return RedirectResponse(url="/openapi.json")


@app.get("/redoc", include_in_schema=False)
async def redoc_endpoint(request: Request):
    """ReDoc docs — requires valid API key."""
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key or api_key != get_settings().api_key:
        return RedirectResponse(url="/docs")
    return RedirectResponse(url="/openapi.json")
