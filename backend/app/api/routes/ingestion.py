"""Ingestion API routes for manual triggers."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.config import Settings, get_settings
from app.ingestion import IngestionService
from app.ingestion.adapters.reddit import RedditAdapter

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


@router.post(
    "/ingestion/trigger",
    response_model=IngestionResult,
    responses={
        503: {"model": IngestionError, "description": "Ingestion failed"},
    },
)
async def trigger_ingestion(
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    platform: str = "reddit",
    limit: int = 100,
) -> IngestionResult:
    """
    Manually trigger ingestion from a platform.

    - **platform**: Data source to fetch from (currently only 'reddit')
    - **limit**: Maximum posts to fetch (default 100)
    """
    if platform != "reddit":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform: {platform}. Only 'reddit' is supported.",
        )

    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Reddit credentials not configured",
        )

    adapter = RedditAdapter()
    try:
        service = IngestionService(session)
        service.register_adapter(adapter)
        result = await service.ingest_from(platform, limit=limit)

        logger.info(
            "Manual ingestion triggered: platform=%s, fetched=%d, upserted=%d",
            platform,
            result.get("fetched", 0),
            result.get("upserted", 0),
        )

        return IngestionResult(
            platform=str(result["platform"]),
            fetched=result["fetched"],
            upserted=result["upserted"],
        )
    except Exception as e:
        logger.error("Manual ingestion failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Ingestion failed: {str(e)}",
        )
    finally:
        await adapter.close()
