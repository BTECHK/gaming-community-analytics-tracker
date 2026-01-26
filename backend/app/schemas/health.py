"""Health check response schema."""

from enum import Enum

from pydantic import BaseModel


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: HealthStatus
    database: str
    cache: str | None = None
    version: str = "0.1.0"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "database": "connected",
                    "cache": "connected",
                    "version": "0.1.0",
                }
            ]
        }
    }
