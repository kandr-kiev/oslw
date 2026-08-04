"""Pydantic schemas for OSLW API."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ============================================================================
# Health
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    wiki_root: str
    wiki_exists: bool


# ============================================================================
# Wiki Page
# ============================================================================

class WikiPageBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field("", max_length=2000)
    type: str = Field(..., pattern="^(concept|comparison|playbook|synthesis|entity|event)$")
    tags: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class WikiPageCreate(WikiPageBase):
    content: str = Field(..., min_length=10)


class WikiPageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    sources: Optional[list[str]] = None


class WikiPageResponse(WikiPageBase):
    slug: str
    created: datetime
    updated: datetime
    content: str
    word_count: int = 0
    line_count: int = 0

    model_config = {"from_attributes": True}


# ============================================================================
# Wiki Doctor
# ============================================================================

class DoctorDiagnostic(BaseModel):
    step: str
    status: str  # "ok", "warning", "error"
    message: str
    count: int = 0


class DoctorReport(BaseModel):
    total_pages: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    steps: list[DoctorDiagnostic] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class DoctorCureRequest(BaseModel):
    dry_run: bool = True
    apply_fixes: bool = False


# ============================================================================
# Graph
# ============================================================================

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "wiki"


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    total: int = 0


# ============================================================================
# Source Monitor
# ============================================================================

class SourceInfo(BaseModel):
    name: str
    type: str  # "rss", "github", "huggingface", "youtube", "local"
    url: str
    last_checked: Optional[datetime] = None
    status: str = "unknown"  # "ok", "error", "pending"
    articles_count: int = 0


class SourceListResponse(BaseModel):
    sources: list[SourceInfo] = Field(default_factory=list)
    total: int = 0


class SourceCheckRequest(BaseModel):
    source_name: Optional[str] = None  # None = check all


# ============================================================================
# Digest
# ============================================================================

class DigestArticle(BaseModel):
    title: str
    slug: str
    summary: str = ""
    created: datetime
    tags: list[str] = Field(default_factory=list)


class DigestResponse(BaseModel):
    date: str
    total_articles: int = 0
    articles: list[DigestArticle] = Field(default_factory=list)


# ============================================================================
# Search
# ============================================================================

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(20, ge=1, le=100)
    type: Optional[str] = None  # filter by page type


class SearchHit(BaseModel):
    slug: str
    title: str
    description: str = ""
    score: float = 0.0
    type: str = ""
    tags: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    total: int = 0
    hits: list[SearchHit] = Field(default_factory=list)
