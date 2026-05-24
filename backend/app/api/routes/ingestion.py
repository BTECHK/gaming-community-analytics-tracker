"""Ingestion API routes for manual triggers and quota monitoring."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.ingestion.adapters import (
    YouTubeAdapter,
    YouTubeQuotaError,
    get_quota_tracker,
    OfficialNewsAdapter,
    TierSiteAdapter,
    GoogleTrendsAdapter,
    GuideSiteAdapter,
    NewsSourceAAdapter,
    NewsSourceBAdapter,
    RedditAdapter,
)
from app.ingestion.service import IngestionService
from app.nlp import NLPService

logger = logging.getLogger(__name__)

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_db)]


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


class SourceStatus(BaseModel):
    """Status of a single ingestion source."""

    enabled: bool
    quota_remaining: int | None = None
    locale: str | None = None
    keywords: int | None = None


class AllSourcesStatus(BaseModel):
    """Status of all ingestion sources."""

    sources: dict[str, SourceStatus]


SUPPORTED_PLATFORMS = {"youtube", "official-news", "tier-site", "google_trends", "guide-site", "news-source-a", "news-source-b", "reddit"}


def _get_adapter(platform: str):
    """Get adapter instance for platform."""
    if platform == "youtube":
        return YouTubeAdapter()
    if platform == "official-news":
        return OfficialNewsAdapter()
    if platform == "tier-site":
        return TierSiteAdapter()
    if platform == "google_trends":
        return GoogleTrendsAdapter()
    if platform == "guide-site":
        return GuideSiteAdapter()
    if platform == "news-source-a":
        return NewsSourceAAdapter()
    if platform == "news-source-b":
        return NewsSourceBAdapter()
    if platform == "reddit":
        return RedditAdapter()
    raise ValueError(f"Unsupported platform: {platform}")


# =============================================================================
# Legacy endpoint (keep for backward compatibility)
# =============================================================================


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

    - **platform**: Data source to fetch from (youtube, official-news, tier-site, google_trends, guide-site)
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

    if platform == "google_trends" and not settings.google_trends_enabled:
        raise HTTPException(
            status_code=501,
            detail="Google Trends ingestion is disabled. Set GOOGLE_TRENDS_ENABLED=true in .env",
        )

    # Check YouTube quota before starting
    if platform == "youtube":
        quota = get_quota_tracker()
        if quota.remaining < 10:
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


# =============================================================================
# Per-source endpoints
# =============================================================================


@router.post("/ingestion/youtube")
async def trigger_youtube_ingestion(session: SessionDep) -> dict:
    """Manually trigger YouTube ingestion.

    Returns summary of ingestion results.
    """
    settings = get_settings()

    if not settings.youtube_api_key:
        raise HTTPException(status_code=503, detail="YouTube API key not configured")

    quota = get_quota_tracker()
    if quota.remaining < 10:
        raise HTTPException(
            status_code=429,
            detail=f"YouTube API quota exceeded. Remaining: {quota.remaining}",
        )

    adapter = YouTubeAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("youtube", limit=settings.youtube_fetch_limit)
        await adapter.close()
        return {
            "source": "youtube",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
            "quota_remaining": get_quota_tracker().remaining,
        }
    except Exception as e:
        logger.error("Manual YouTube ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/official-news")
async def trigger_official_news_ingestion(session: SessionDep) -> dict:
    """Manually trigger OfficialNews news ingestion."""
    settings = get_settings()

    adapter = OfficialNewsAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("official-news", limit=settings.official_news_fetch_limit)
        await adapter.close()
        return {
            "source": "official-news",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual OfficialNews ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/tier-site")
async def trigger_tiersite_ingestion(session: SessionDep) -> dict:
    """Manually trigger TierSite tier list ingestion."""
    settings = get_settings()

    adapter = TierSiteAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("tier-site", limit=settings.tiersite_fetch_limit)
        await adapter.close()
        return {
            "source": "tier-site",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual TierSite ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/google-trends")
async def trigger_google_trends_ingestion(session: SessionDep) -> dict:
    """Manually trigger Google Trends ingestion.

    Note: This endpoint may take several minutes due to rate limiting (60s between requests).
    Limited to 4 keywords per request.
    """
    settings = get_settings()

    if not settings.google_trends_enabled:
        raise HTTPException(status_code=503, detail="Google Trends ingestion is disabled")

    adapter = GoogleTrendsAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("google_trends", limit=4)
        await adapter.close()
        return {
            "source": "google_trends",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
            "note": "Limited to 4 keywords due to rate limiting",
        }
    except Exception as e:
        logger.error("Manual Google Trends ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/guide-site")
async def trigger_guidesite_ingestion(session: SessionDep) -> dict:
    """Manually trigger GuideSite guide ingestion."""
    settings = get_settings()

    adapter = GuideSiteAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("guide-site", limit=settings.guidesite_fetch_limit)
        await adapter.close()
        return {
            "source": "guide-site",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual GuideSite ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/news-source-a")
async def trigger_newssource_a_ingestion(session: SessionDep) -> dict:
    """Manually trigger NewsSourceA article ingestion."""
    settings = get_settings()

    adapter = NewsSourceAAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("news-source-a", limit=settings.newssource_a_fetch_limit)
        await adapter.close()
        return {
            "source": "news-source-a",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual NewsSourceA ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/news-source-b")
async def trigger_newssource_b_ingestion(session: SessionDep) -> dict:
    """Manually trigger News Source B article ingestion."""
    settings = get_settings()

    adapter = NewsSourceBAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("news-source-b", limit=settings.newssource_b_fetch_limit)
        await adapter.close()
        return {
            "source": "news-source-b",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual News Source B ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingestion/reddit")
async def trigger_reddit_ingestion(session: SessionDep) -> dict:
    """Manually trigger Reddit post ingestion."""
    settings = get_settings()

    adapter = RedditAdapter()
    service = IngestionService(session)
    service.register_adapter(adapter)

    try:
        result = await service.ingest_from("reddit", limit=settings.reddit_fetch_limit)
        await adapter.close()
        return {
            "source": "reddit",
            "status": "complete",
            "fetched": result.get("fetched", 0),
            "upserted": result.get("upserted", 0),
        }
    except Exception as e:
        logger.error("Manual Reddit ingestion failed: %s", e)
        await adapter.close()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Status endpoints
# =============================================================================


@router.get("/ingestion/status")
async def get_ingestion_status() -> AllSourcesStatus:
    """Get status of all ingestion sources."""
    settings = get_settings()

    youtube_quota = get_quota_tracker() if settings.youtube_api_key else None

    return AllSourcesStatus(
        sources={
            "youtube": SourceStatus(
                enabled=bool(settings.youtube_api_key),
                quota_remaining=youtube_quota.remaining if youtube_quota else None,
            ),
            "official-news": SourceStatus(
                enabled=True,
                locale=settings.official_news_locale,
            ),
            "tier-site": SourceStatus(
                enabled=True,
            ),
            "google_trends": SourceStatus(
                enabled=settings.google_trends_enabled,
                keywords=len(settings.google_trends_keywords_list),
            ),
            "guide-site": SourceStatus(
                enabled=True,
            ),
            "news-source-a": SourceStatus(
                enabled=True,
            ),
            "news-source-b": SourceStatus(
                enabled=True,
            ),
            "reddit": SourceStatus(
                enabled=True,
            ),
        }
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
    if platform != "youtube":
        raise HTTPException(
            status_code=400,
            detail=f"No quota tracking for {platform}. Only YouTube has quota tracking.",
        )

    quota = get_quota_tracker()
    settings = get_settings()
    return QuotaStatus(
        platform="youtube",
        used=quota.used,
        remaining=quota.remaining,
        daily_limit=settings.youtube_daily_quota_limit,
    )


# =============================================================================
# NLP endpoints
# =============================================================================


class NLPStatusResponse(BaseModel):
    """Response model for NLP status."""

    total_posts: int
    with_valid_sentiment: int
    needs_analysis: int
    config: dict


class NLPSentimentResponse(BaseModel):
    """Response model for sentiment analysis trigger."""

    processed: int
    filtered_toxic: int
    status: str


@router.get("/ingestion/nlp-stats")
async def get_nlp_stats(session: SessionDep) -> NLPStatusResponse:
    """Get NLP processing status and configuration.

    Returns statistics on posts with/without sentiment analysis
    and current NLP configuration settings.
    """
    service = NLPService(session)
    stats = await service.get_stats()

    return NLPStatusResponse(
        total_posts=stats["total_posts"],
        with_valid_sentiment=stats["with_valid_sentiment"],
        needs_analysis=stats["needs_analysis"],
        config=stats["config"],
    )


@router.post("/ingestion/nlp-sentiment")
async def trigger_sentiment_analysis(session: SessionDep) -> NLPSentimentResponse:
    """Manually trigger sentiment analysis on unprocessed posts.

    Processes posts that either have no sentiment result or have
    an expired sentiment result (past TTL).

    Returns the number of posts processed.
    """
    settings = get_settings()

    if not settings.nlp_enabled:
        raise HTTPException(
            status_code=503,
            detail="NLP pipeline is disabled. Set NLP_ENABLED=true in .env",
        )

    try:
        service = NLPService(session)
        result = await service.process_batch()

        return NLPSentimentResponse(
            processed=result["processed"],
            filtered_toxic=result["filtered_toxic"],
            status=result["status"],
        )
    except Exception as e:
        logger.error("Manual sentiment analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
