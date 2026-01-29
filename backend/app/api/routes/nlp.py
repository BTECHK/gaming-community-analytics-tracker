"""NLP API routes for manual job triggering, status, and health checks."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.nlp.jobs import get_job_manager
from app.nlp.health import get_nlp_health, get_nlp_health_detailed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlp")


@router.post("/trigger")
async def trigger_nlp_job() -> dict[str, Any]:
    """Trigger a manual NLP processing job.

    Rate limited to 1 request per 5 minutes.

    Returns:
        Job status information.

    Raises:
        HTTPException: If job cannot be started (rate limited or already running).
    """
    manager = get_job_manager()

    can_start, reason = manager.can_trigger()
    if not can_start:
        raise HTTPException(status_code=429, detail=reason)

    try:
        job = await manager.trigger_job()
        logger.info("Manual NLP job triggered: %s", job.job_id)
        return {
            "status": "started",
            "job_id": job.job_id,
            "message": "NLP processing job started",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/status")
async def get_nlp_status() -> dict[str, Any]:
    """Get current NLP job status.

    Returns:
        Job status information including progress if running.
    """
    manager = get_job_manager()
    return manager.get_status()


@router.delete("/cancel")
async def cancel_nlp_job() -> dict[str, Any]:
    """Cancel the currently running NLP job.

    Returns:
        Cancellation status.

    Raises:
        HTTPException: If no job is running.
    """
    manager = get_job_manager()

    if not manager.is_running:
        raise HTTPException(status_code=404, detail="No job is currently running")

    cancelled = await manager.cancel_job()
    if cancelled:
        logger.info("NLP job cancellation requested")
        return {
            "status": "cancelling",
            "message": "Cancellation requested. Job will stop after current batch.",
        }
    else:
        raise HTTPException(status_code=404, detail="No job is currently running")


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """Get NLP system health status.

    Returns lightweight health check for frequent polling.

    Returns:
        Health status including memory, circuit breakers, and job status.
    """
    return get_nlp_health()


@router.get("/health/detailed")
async def get_health_detailed() -> dict[str, Any]:
    """Get detailed NLP system health including model checks.

    This endpoint is more expensive as it tests model loading.
    Use for diagnostics, not frequent polling.

    Returns:
        Detailed health status including model status.
    """
    return get_nlp_health_detailed()
