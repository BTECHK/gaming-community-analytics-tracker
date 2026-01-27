"""APScheduler configuration for periodic ingestion jobs."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.ingestion.adapters import (
    YouTubeAdapter,
    get_quota_tracker,
    RiotAdapter,
    TierSiteAdapter,
    GoogleTrendsAdapter,
    GuideSiteAdapter,
)
from app.ingestion.service import IngestionService
from app.nlp import NLPService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def youtube_ingestion_job() -> None:
    """Scheduled job to ingest videos from YouTube.

    Runs every 6 hours, fetches from configured channels.
    Skips if API key not configured.
    """
    settings = get_settings()

    if not settings.youtube_api_key:
        logger.info("YouTube API key not configured, skipping scheduled ingestion")
        return

    logger.info("Starting scheduled YouTube ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = YouTubeAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            result = await service.ingest_from("youtube", limit=settings.youtube_fetch_limit)

            logger.info(
                "YouTube ingestion complete: fetched=%d, upserted=%d, quota_remaining=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
                get_quota_tracker().remaining,
            )

            await adapter.close()
        except Exception as e:
            logger.error("YouTube ingestion job failed: %s", e)
        finally:
            await session.close()


async def riot_ingestion_job() -> None:
    """Scheduled job to ingest OfficialNews news."""
    logger.info("Starting scheduled OfficialNews ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = RiotAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("official-news", limit=settings.riot_fetch_limit)

            logger.info(
                "OfficialNews ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("OfficialNews ingestion job failed: %s", e)
        finally:
            await session.close()


async def tiersite_ingestion_job() -> None:
    """Scheduled job to ingest TierSite tier lists."""
    logger.info("Starting scheduled TierSite ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = TierSiteAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("tier-site", limit=settings.tiersite_fetch_limit)

            logger.info(
                "TierSite ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("TierSite ingestion job failed: %s", e)
        finally:
            await session.close()


async def google_trends_ingestion_job() -> None:
    """Scheduled job to ingest Google Trends data.

    Note: This job has long delays (60s between requests) and may take several minutes.
    """
    settings = get_settings()

    if not settings.google_trends_enabled:
        logger.info("Google Trends disabled, skipping scheduled ingestion")
        return

    logger.info("Starting scheduled Google Trends ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = GoogleTrendsAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            # Limit to 4 keywords per run (4 * 60s = 4 minutes)
            result = await service.ingest_from("google_trends", limit=4)

            logger.info(
                "Google Trends ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("Google Trends ingestion job failed: %s", e)
        finally:
            await session.close()


async def guidesite_ingestion_job() -> None:
    """Scheduled job to ingest GuideSite guides."""
    logger.info("Starting scheduled GuideSite ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = GuideSiteAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("guide-site", limit=settings.guidesite_fetch_limit)

            logger.info(
                "GuideSite ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("GuideSite ingestion job failed: %s", e)
        finally:
            await session.close()


async def sentiment_analysis_job() -> None:
    """Scheduled job to run sentiment analysis on unprocessed posts.

    Runs every 6 hours with 30min offset to ensure ingestion completes first.
    """
    settings = get_settings()

    if not settings.nlp_enabled:
        logger.info("NLP pipeline disabled, skipping sentiment analysis")
        return

    logger.info("Starting scheduled sentiment analysis")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            service = NLPService(session)
            result = await service.process_batch()

            logger.info(
                "Sentiment analysis complete: processed=%d",
                result.get("processed", 0),
            )
        except Exception as e:
            logger.error("Sentiment analysis job failed: %s", e)
        finally:
            await session.close()


def configure_scheduler() -> None:
    """Configure scheduler with ingestion jobs."""
    settings = get_settings()

    # YouTube job (only if API key is configured)
    if settings.youtube_api_key:
        scheduler.add_job(
            youtube_ingestion_job,
            "interval",
            hours=6,
            id="youtube_ingestion",
            name="YouTube Video Ingestion",
            replace_existing=True,
        )
        logger.info("Scheduled YouTube ingestion job (every 6 hours)")
    else:
        logger.info("YouTube API key not configured, skipping job registration")

    # OfficialNews job (always enabled - no API key needed)
    scheduler.add_job(
        riot_ingestion_job,
        "interval",
        hours=6,
        id="riot_ingestion",
        name="OfficialNews News Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled OfficialNews ingestion job (every 6 hours)")

    # TierSite job (always enabled)
    scheduler.add_job(
        tiersite_ingestion_job,
        "interval",
        hours=6,
        id="tier-site_ingestion",
        name="TierSite Tier List Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled TierSite ingestion job (every 6 hours)")

    # Google Trends job (configurable)
    if settings.google_trends_enabled:
        scheduler.add_job(
            google_trends_ingestion_job,
            "interval",
            hours=12,  # Less frequent due to rate limits
            id="google_trends_ingestion",
            name="Google Trends Ingestion",
            replace_existing=True,
        )
        logger.info("Scheduled Google Trends ingestion job (every 12 hours)")
    else:
        logger.info("Google Trends disabled, skipping job registration")

    # GuideSite job (always enabled)
    scheduler.add_job(
        guidesite_ingestion_job,
        "interval",
        hours=6,
        id="guide-site_ingestion",
        name="GuideSite Guide Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled GuideSite ingestion job (every 6 hours)")

    # Sentiment analysis job (configurable, runs with offset after ingestion)
    if settings.nlp_enabled:
        scheduler.add_job(
            sentiment_analysis_job,
            "interval",
            hours=6,
            minutes=30,  # 30min offset to run after ingestion jobs complete
            id="sentiment_analysis",
            name="Sentiment Analysis",
            replace_existing=True,
        )
        logger.info("Scheduled sentiment analysis job (every 6 hours + 30min offset)")
    else:
        logger.info("NLP pipeline disabled, skipping sentiment analysis job")


@asynccontextmanager
async def scheduler_lifespan() -> AsyncIterator[None]:
    """Async context manager for scheduler lifecycle."""
    configure_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
