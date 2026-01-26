"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas.health import HealthResponse, HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbSession) -> HealthResponse:
    """
    Health check endpoint that verifies database connectivity.

    Returns:
        HealthResponse with status and component health
    """
    db_status = "disconnected"
    overall_status = HealthStatus.UNHEALTHY

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        overall_status = HealthStatus.HEALTHY
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        overall_status = HealthStatus.UNHEALTHY

    # TODO: Add Valkey check in future phase
    cache_status = None

    return HealthResponse(
        status=overall_status,
        database=db_status,
        cache=cache_status,
    )
