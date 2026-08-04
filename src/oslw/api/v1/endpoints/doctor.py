"""WikiDoctor endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from oslw.api.v1.schemas import (
    DoctorReport,
    DoctorCureRequest,
)
from oslw.config.logging import get_logger

router = APIRouter(tags=["doctor"])
logger = get_logger("api.doctor")


@router.get(
    "/diagnose",
    response_model=DoctorReport,
    summary="Diagnose wiki",
    description="Run WikiDoctor diagnosis on the wiki",
)
async def diagnose_wiki(
    layers: Optional[str] = Query(
        None,
        description="Specific layers to check (comma-separated: index,wiki_pages,metadata)",
    ),
) -> DoctorReport:
    """Run WikiDoctor diagnosis."""
    # TODO: Implement actual diagnosis
    logger.info("Running wiki diagnosis")
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )


@router.post(
    "/cure",
    summary="Cure wiki",
    description="Run WikiDoctor cure operations",
)
async def cure_wiki(request: DoctorCureRequest) -> dict:
    """Run WikiDoctor cure operations."""
    # TODO: Implement actual cure
    logger.info("Running wiki cure: dry_run=%s, apply_fixes=%s", request.dry_run, request.apply_fixes)
    raise HTTPException(
        status_code=501,
        detail="Not implemented - domain layer in progress",
    )
