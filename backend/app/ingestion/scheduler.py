"""APScheduler configuration for periodic ingestion jobs."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import get_session_factory
from app.ingestion import IngestionService
from app.ingestion.adapters.reddit import RedditAdapter

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def scheduled_reddit_fetch() -> None:
    """Background task to fetch Reddit posts."""
    settings = get_settings()

    # Skip if no credentials configured
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        logger.warning("Reddit credentials not configured, skipping scheduled fetch")
        return

    logger.info("Starting scheduled Reddit fetch")

    session_factory = get_session_factory()
    async with session_factory() as session:
        adapter = RedditAdapter()
        try:
            service = IngestionService(session)
            service.register_adapter(adapter)
            result = await service.ingest_from("reddit", limit=settings.reddit_fetch_limit)
            logger.info(
                "Scheduled fetch complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )
        except Exception as e:
            logger.error("Scheduled Reddit fetch failed: %s", e, exc_info=True)
        finally:
            await adapter.close()


def configure_scheduler() -> None:
    """Configure scheduler with ingestion jobs."""
    settings = get_settings()

    scheduler.add_job(
        scheduled_reddit_fetch,
        IntervalTrigger(minutes=settings.reddit_fetch_interval_minutes),
        id="reddit_fetch",
        name="Fetch Reddit posts from r/gamecommunity",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    logger.info(
        "Configured Reddit fetch job (interval=%d minutes)",
        settings.reddit_fetch_interval_minutes,
    )


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
