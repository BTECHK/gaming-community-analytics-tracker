"""Ingestion API routes for manual triggers.

Note: Reddit adapter was removed from scope (2026-01-26).
This module will be updated in Phase 2 to support YouTube ingestion.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
        501: {"model": IngestionError, "description": "Not implemented"},
    },
)
async def trigger_ingestion(
    platform: str = "youtube",
    limit: int = 100,
) -> IngestionResult:
    """
    Manually trigger ingestion from a platform.

    - **platform**: Data source to fetch from (youtube coming in Phase 2)
    - **limit**: Maximum posts to fetch (default 100)

    Note: Currently not implemented. Phase 2 (YouTube Ingestion) will add support.
    """
    raise HTTPException(
        status_code=501,
        detail=f"Platform '{platform}' not yet implemented. Coming in Phase 2.",
    )
