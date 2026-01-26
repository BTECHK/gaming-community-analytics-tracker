"""APScheduler configuration for periodic ingestion jobs.

Note: Reddit adapter was removed from scope (2026-01-26).
This module will be updated in Phase 2 to support YouTube ingestion.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    """Configure scheduler with ingestion jobs.

    Currently a placeholder - will be configured in Phase 2 (YouTube Ingestion).
    """
    logger.info("Scheduler configured (no jobs registered yet - Phase 2 pending)")


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
