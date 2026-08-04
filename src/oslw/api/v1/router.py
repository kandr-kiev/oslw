"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from oslw.api.v1.endpoints import health, wiki, sources, graph, doctor, digest, search

api_router = APIRouter()

# Health
api_router.include_router(health.router, tags=["health"])

# Wiki
api_router.include_router(wiki.router, prefix="/wiki", tags=["wiki"])

# Sources
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])

# Graph
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])

# Doctor
api_router.include_router(doctor.router, prefix="/doctor", tags=["doctor"])

# Digest
api_router.include_router(digest.router, prefix="/digest", tags=["digest"])

# Search
api_router.include_router(search.router, prefix="/search", tags=["search"])
