"""Ingestion API routes for manual triggers and quota monitoring."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.ingestion.adapters import (
    YouTubeAdapter,
    YouTubeQuotaError,
    get_quota_tracker,
)
from app.ingestion.service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestionResult(BaseModel):
    """Response model for ingestion trigger."""

    platform: str
    fetched: int
    upserted: int


class IngestionError(BaseModel):
    """Response model for ingestion error."""

    platform: str
    error: str


class QuotaStatus(BaseModel):
    """Response model for quota status."""

    platform: str
    used: int
    remaining: int
    daily_limit: int


SUPPORTED_PLATFORMS = {"youtube"}


def _get_adapter(platform: str):
    """Get adapter instance for platform."""
    if platform == "youtube":
        return YouTubeAdapter()
    raise ValueError(f"Unsupported platform: {platform}")


@router.post(
    "/ingestion/trigger",
    response_model=IngestionResult,
    responses={
        400: {"model": IngestionError, "description": "Bad request"},
        429: {"model": IngestionError, "description": "Quota exceeded"},
        501: {"model": IngestionError, "description": "Not configured"},
    },
)
async def trigger_ingestion(
    platform: str = "youtube",
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> IngestionResult:
    """
    Manually trigger ingestion from a platform.

    - **platform**: Data source to fetch from (currently: youtube)
    - **limit**: Maximum posts to fetch (default 100)

    Returns 429 if quota exceeded, 501 if platform not configured.
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform: {platform}. Supported: {SUPPORTED_PLATFORMS}",
        )

    settings = get_settings()

    # Check if platform is configured
    if platform == "youtube" and not settings.youtube_api_key:
        raise HTTPException(
            status_code=501,
            detail="YouTube API key not configured. Set YOUTUBE_API_KEY in .env",
        )

    # Check quota before starting
    quota = get_quota_tracker()
    if quota.remaining < 10:  # Need at least some quota for basic operations
        raise HTTPException(
            status_code=429,
            detail=f"YouTube API quota exceeded. Remaining: {quota.remaining}",
        )

    try:
        adapter = _get_adapter(platform)
        service = IngestionService(session)
        service.register_adapter(adapter)

        result = await service.ingest_from(platform, limit=limit)

        await adapter.close()

        return IngestionResult(
            platform=result["platform"],
            fetched=result["fetched"],
            upserted=result["upserted"],
        )

    except YouTubeQuotaError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Ingestion failed for %s: %s", platform, e)
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {e}",
        )


@router.get(
    "/ingestion/quota",
    response_model=QuotaStatus,
    responses={
        400: {"model": IngestionError, "description": "Bad request"},
    },
)
async def get_quota_status(platform: str = "youtube") -> QuotaStatus:
    """
    Get API quota status for a platform.

    - **platform**: Platform to check quota for (currently: youtube)

    Returns current quota usage and remaining units.
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform: {platform}. Supported: {SUPPORTED_PLATFORMS}",
        )

    if platform == "youtube":
        quota = get_quota_tracker()
        settings = get_settings()
        return QuotaStatus(
            platform="youtube",
            used=quota.used,
            remaining=quota.remaining,
            daily_limit=settings.youtube_daily_quota_limit,
        )

    # Should not reach here due to earlier check
    raise HTTPException(status_code=400, detail=f"No quota tracking for {platform}")
