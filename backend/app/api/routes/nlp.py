"""NLP API routes for manual job triggering, status, and health checks."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.nlp.jobs import get_job_manager
from app.nlp.health import get_nlp_health, get_nlp_health_detailed
from app.nlp.dead_letter import DeadLetterQueue

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

    can_start, reason = await manager.can_trigger()
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
    return await manager.get_status()


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
    return await get_nlp_health()


@router.get("/health/detailed")
async def get_health_detailed() -> dict[str, Any]:
    """Get detailed NLP system health including model checks.

    This endpoint is more expensive as it tests model loading.
    Use for diagnostics, not frequent polling.

    Returns:
        Detailed health status including model status.
    """
    return await get_nlp_health_detailed()


@router.get("/dlq")
async def get_dlq_posts(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Get list of posts in the dead letter queue.

    Args:
        limit: Maximum number of posts to return (default 100).
        offset: Number of posts to skip for pagination.

    Returns:
        List of failed posts with their error details.
    """
    try:
        dlq = await DeadLetterQueue.get_instance()
        posts = await dlq.get_failed_posts(limit=limit, offset=offset)
        stats = await dlq.get_stats()

        return {
            "posts": posts,
            "stats": stats,
            "pagination": {
                "limit": limit,
                "offset": offset,
            },
        }
    except Exception as e:
        logger.error("Failed to get DLQ posts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ data")


@router.get("/dlq/{post_id}")
async def get_dlq_post_details(post_id: str) -> dict[str, Any]:
    """Get detailed information about a specific failed post.

    Args:
        post_id: The post identifier.

    Returns:
        Full details including error history.

    Raises:
        HTTPException: If post not found in DLQ.
    """
    try:
        dlq = await DeadLetterQueue.get_instance()
        details = await dlq.get_post_details(post_id)

        if details is None:
            raise HTTPException(status_code=404, detail="Post not found in DLQ")

        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get DLQ post details: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve post details")


@router.delete("/dlq/{post_id}")
async def remove_dlq_post(post_id: str) -> dict[str, Any]:
    """Remove a specific post from the dead letter queue.

    Args:
        post_id: The post identifier.

    Returns:
        Removal status.

    Raises:
        HTTPException: If post not found in DLQ.
    """
    try:
        dlq = await DeadLetterQueue.get_instance()
        removed = await dlq.remove_post(post_id)

        if not removed:
            raise HTTPException(status_code=404, detail="Post not found in DLQ")

        logger.info("Removed post %s from DLQ", post_id)
        return {
            "status": "removed",
            "post_id": post_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove post from DLQ: %s", e)
        raise HTTPException(status_code=500, detail="Failed to remove post from DLQ")


@router.delete("/dlq")
async def clear_dlq() -> dict[str, Any]:
    """Clear all entries from the dead letter queue.

    Returns:
        Number of entries cleared.
    """
    try:
        dlq = await DeadLetterQueue.get_instance()
        count = await dlq.clear()

        logger.info("Cleared %d entries from DLQ", count)
        return {
            "status": "cleared",
            "entries_removed": count,
        }
    except Exception as e:
        logger.error("Failed to clear DLQ: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clear DLQ")
