"""WikiDoctor endpoints — wiki health diagnostics and repair.

Uses QualityService from Application Layer.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from oslw.api.v1.schemas import (
    DoctorReport,
    DoctorDiagnostic,
    DoctorCureRequest,
)
from oslw.api.deps import get_settings, get_api_key
from oslw.config.settings import Settings
from oslw.application import QualityService
from oslw.config.logging import get_logger

router = APIRouter(tags=["doctor"])
logger = get_logger("api.doctor")


def get_quality_service(settings: Settings = Depends(get_settings)) -> QualityService:
    """Dependency injection for QualityService."""
    return QualityService(wiki_root=settings.wiki_root)


@router.get(
    "/diagnose",
    response_model=DoctorReport,
    summary="Diagnose wiki",
    description="Run WikiDoctor diagnosis on the wiki",
)
def diagnose_wiki(
    layers: Optional[str] = Query(
        None,
        description="Specific layers to check (comma-separated: index,wiki_pages,metadata)",
    ),
    quality_service: QualityService = Depends(get_quality_service),
) -> DoctorReport:
    """Run WikiDoctor diagnosis."""
    try:
        layer = "all"
        if layers:
            layer = layers

        audit = quality_service.run_full_audit()
        diagnosis = audit["diagnosis"]
        quality = audit["quality_stats"]

        steps = []

        # Add diagnosis steps
        for severity in ["critical", "warning", "info"]:
            count = diagnosis["severity_counts"].get(severity, 0)
            if count > 0:
                steps.append(DoctorDiagnostic(
                    step=f"{severity}_issues",
                    status="error" if severity == "critical" else ("warning" if severity == "warning" else "ok"),
                    message=f"Found {count} {severity} issues",
                    count=count,
                ))

        # Add quality steps
        steps.append(DoctorDiagnostic(
            step="frontmatter_coverage",
            status="ok" if quality["pages_with_frontmatter"] == quality["total_pages"] else "warning",
            message=f"{quality['pages_with_frontmatter']}/{quality['total_pages']} pages have frontmatter",
            count=quality["pages_with_frontmatter"],
        ))

        steps.append(DoctorDiagnostic(
            step="sha256_integrity",
            status="ok" if quality["pages_with_sha256"] == quality["total_pages"] else "warning",
            message=f"{quality['pages_with_sha256']}/{quality['total_pages']} pages have SHA256",
            count=quality["pages_with_sha256"],
        ))

        steps.append(DoctorDiagnostic(
            step="orphan_pages",
            status="warning" if quality["orphan_pages"] > 0 else "ok",
            message=f"{quality['orphan_pages']} orphan pages found",
            count=quality["orphan_pages"],
        ))

        steps.append(DoctorDiagnostic(
            step="duplicate_detection",
            status="warning" if quality["duplicate_groups"] > 0 else "ok",
            message=f"{quality['duplicate_groups']} duplicate groups found",
            count=quality["duplicate_groups"],
        ))

        total_errors = diagnosis["severity_counts"].get("critical", 0)
        total_warnings = diagnosis["severity_counts"].get("warning", 0)

        return DoctorReport(
            total_pages=quality["total_pages"],
            total_errors=total_errors,
            total_warnings=total_warnings,
            steps=steps,
            summary={
                "health_score": quality["pages_with_sha256"] / quality["total_pages"] if quality["total_pages"] > 0 else 1.0,
                "orphan_pages": quality["orphan_pages"],
                "duplicates": quality["duplicate_groups"],
            },
        )
    except Exception as e:
        logger.error("Помилка діагностики wiki: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cure",
    summary="Cure wiki",
    description="Run WikiDoctor cure operations",
)
def cure_wiki(
    request: DoctorCureRequest,
    quality_service: QualityService = Depends(get_quality_service),
    api_key: str = Depends(get_api_key),
) -> dict:
    """Run WikiDoctor cure operations."""
    try:
        results = {}

        # Fix broken wikilinks
        duplicates_removed = quality_service.cleanup_duplicates(dry_run=not request.apply_fixes)
        results["duplicates"] = {
            "removed": duplicates_removed,
            "dry_run": request.dry_run,
        }

        # Run diagnosis after cure
        report = diagnose_wiki(layers=None, quality_service=quality_service)

        results["diagnosis_after"] = {
            "total_errors": report.total_errors,
            "total_warnings": report.total_warnings,
            "total_pages": report.total_pages,
        }

        return {
            "success": True,
            "results": results,
            "dry_run": request.dry_run,
        }
    except Exception as e:
        logger.error("Помилка лікування wiki: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
