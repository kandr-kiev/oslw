"""Background task routes for OSLW API.

Provides async background execution for expensive operations:
- POST /api/bg/graph/generate - generate graph in background
- POST /api/bg/audit/run - run full audit in background
- GET /api/bg/status/{task_id} - check task status
- GET /api/bg/results/{task_id} - get task results
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from oslw.application import GraphService, QualityService
from oslw.config.settings import settings
from oslw.config.logging import get_logger

logger = get_logger("oslw.api.background")

router = APIRouter(prefix="/bg", tags=["background-tasks"])

# In-memory task store (for single-process deployment)
# In production, use Redis or a database
_task_store: dict[str, dict] = {}


def _get_task_store() -> dict[str, dict]:
    """Get the task store singleton."""
    return _task_store


@router.post("/graph/generate", summary="Generate graph in background")
async def bg_generate_graph(
    background_tasks: BackgroundTasks,
    force: bool = False,
    export_to_disk: bool = True,
):
    """Generate knowledge graph in background.

    Useful for large wikis where graph generation takes >10 seconds.
    Returns a task_id to check status and retrieve results.
    """
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "type": "graph_generate",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }
    _get_task_store()[task_id] = task

    background_tasks.add_task(
        _run_graph_generate,
        task_id,
        force,
        export_to_disk,
    )

    return {
        "task_id": task_id,
        "type": "graph_generate",
        "status": "pending",
        "message": "Graph generation started in background",
    }


@router.post("/audit/run", summary="Run full audit in background")
async def bg_run_audit(
    background_tasks: BackgroundTasks,
    sample_size: Optional[int] = 100,
):
    """Run full quality audit in background.

    Useful for large wikis where audit takes >30 seconds.
    Returns a task_id to check status and retrieve results.
    """
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "type": "audit_run",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }
    _get_task_store()[task_id] = task

    background_tasks.add_task(
        _run_audit,
        task_id,
        sample_size,
    )

    return {
        "task_id": task_id,
        "type": "audit_run",
        "status": "pending",
        "message": "Audit started in background",
    }


@router.get("/status/{task_id}", summary="Check background task status")
async def get_task_status(task_id: str):
    """Check the status of a background task.

    Returns task status, progress, and result if completed.
    """
    task = _get_task_store().get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return {
        "task_id": task_id,
        "type": task["type"],
        "status": task["status"],
        "created_at": task["created_at"],
        "result": task["result"],
        "error": task["error"],
    }


@router.get("/results/{task_id}", summary="Get background task results")
async def get_task_results(task_id: str):
    """Get the results of a completed background task."""
    task = _get_task_store().get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed (status: {task['status']})",
        )

    return {
        "task_id": task_id,
        "type": task["type"],
        "status": task["status"],
        "result": task["result"],
    }


def _run_graph_generate(task_id: str, force: bool, export_to_disk: bool) -> None:
    """Run graph generation as a background task."""
    task = _get_task_store().get(task_id)
    if not task:
        return

    try:
        task["status"] = "running"
        svc = GraphService(wiki_root=settings.wiki_root)
        graph = svc.generate_graph(force=force)

        if export_to_disk:
            path = svc.export_graph()
            task["result"] = {
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("edges", [])),
                "export_path": str(path),
            }
        else:
            task["result"] = {
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("edges", [])),
            }

        task["status"] = "completed"
        logger.info("Background graph generation %s completed", task_id)

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        logger.error("Background graph generation %s failed: %s", task_id, e)


def _run_audit(task_id: str, sample_size: Optional[int]) -> None:
    """Run full quality audit as a background task."""
    task = _get_task_store().get(task_id)
    if not task:
        return

    try:
        task["status"] = "running"
        svc = QualityService(wiki_root=settings.wiki_root)
        result = svc.run_full_audit(sample_size=sample_size)

        task["result"] = result
        task["status"] = "completed"
        logger.info("Background audit %s completed", task_id)

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        logger.error("Background audit %s failed: %s", task_id, e)
