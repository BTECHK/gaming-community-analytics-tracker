"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.ingestion.scheduler import get_scheduler
from app.nlp.valkey_store import ValkeyJobStore
from app.schemas.health import HealthResponse, HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbSession) -> HealthResponse:
    """
    Health check endpoint that verifies database, cache, and scheduler status.

    Returns:
        HealthResponse with status and component health
    """
    db_status = "disconnected"
    cache_status = "disconnected"
    scheduler_status = "not initialized"
    overall_status = HealthStatus.UNHEALTHY

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        overall_status = HealthStatus.HEALTHY
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        overall_status = HealthStatus.UNHEALTHY

    # Check Valkey cache
    try:
        valkey = await ValkeyJobStore.get_instance()
        health = await valkey.health_check()
        cache_status = health.get("status", "error")
    except Exception as e:
        cache_status = f"error: {str(e)[:100]}"

    # Check scheduler status
    try:
        sched = get_scheduler()
        if sched.running:
            job_count = len(sched.get_jobs())
            scheduler_status = f"running ({job_count} jobs)"
        else:
            scheduler_status = "stopped"
            # Degrade status if scheduler not running
            if overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
    except Exception as e:
        scheduler_status = f"error: {str(e)[:100]}"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        cache=cache_status,
        scheduler=scheduler_status,
    )
