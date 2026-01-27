"""APScheduler configuration for periodic ingestion jobs."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.ingestion.adapters import YouTubeAdapter, get_quota_tracker
from app.ingestion.service import IngestionService

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


def configure_scheduler() -> None:
    """Configure scheduler with ingestion jobs."""
    settings = get_settings()

    # Only add YouTube job if API key is configured
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
