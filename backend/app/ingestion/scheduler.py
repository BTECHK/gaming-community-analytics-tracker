"""APScheduler configuration for periodic ingestion jobs."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.ingestion.adapters import (
    YouTubeAdapter,
    get_quota_tracker,
    RiotAdapter,
    TierSiteAdapter,
    GoogleTrendsAdapter,
    GuideSiteAdapter,
    NewsSourceAAdapter,
    NewsSourceBAdapter,
    RedditAdapter,
)
from app.ingestion.service import IngestionService
from app.nlp import NLPService
from app.nlp.dead_letter import DeadLetterQueue
from app.dashboard import AggregationService
from app.models import Post

logger = logging.getLogger(__name__)

# Global scheduler instance - initialized lazily to ensure event loop exists
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance.

    Creates the scheduler lazily to ensure the event loop exists when
    the scheduler is instantiated. This prevents issues with APScheduler
    trying to get an event loop that doesn't exist yet.
    """
    global _scheduler
    if _scheduler is None:
        # Get the current event loop to pass to the scheduler
        try:
            loop = asyncio.get_running_loop()
            _scheduler = AsyncIOScheduler(event_loop=loop)
            logger.debug("Created AsyncIOScheduler with event loop")
        except RuntimeError:
            # No running loop, create scheduler without explicit loop
            # (APScheduler will get the loop when start() is called)
            _scheduler = AsyncIOScheduler()
            logger.debug("Created AsyncIOScheduler without explicit event loop")
    return _scheduler


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


async def newssource_a_ingestion_job() -> None:
    """Scheduled job to ingest NewsSourceA the game articles."""
    logger.info("Starting scheduled NewsSourceA ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = NewsSourceAAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("news-source-a", limit=settings.newssource_a_fetch_limit)

            logger.info(
                "NewsSourceA ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("NewsSourceA ingestion job failed: %s", e)
        finally:
            await session.close()


async def newssource_b_ingestion_job() -> None:
    """Scheduled job to ingest News Source B the game articles."""
    logger.info("Starting scheduled News Source B ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = NewsSourceBAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("news-source-b", limit=settings.newssource_b_fetch_limit)

            logger.info(
                "News Source B ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("News Source B ingestion job failed: %s", e)
        finally:
            await session.close()


async def reddit_ingestion_job() -> None:
    """Scheduled job to ingest Reddit posts from configured subreddits."""
    logger.info("Starting scheduled Reddit ingestion")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            adapter = RedditAdapter()
            service = IngestionService(session)
            service.register_adapter(adapter)

            settings = get_settings()
            result = await service.ingest_from("reddit", limit=settings.reddit_fetch_limit)

            logger.info(
                "Reddit ingestion complete: fetched=%d, upserted=%d",
                result.get("fetched", 0),
                result.get("upserted", 0),
            )

            await adapter.close()
        except Exception as e:
            logger.error("Reddit ingestion job failed: %s", e)
        finally:
            await session.close()


async def sentiment_analysis_job() -> None:
    """Scheduled job to run sentiment analysis on unprocessed posts.

    Runs every 6 hours with 30min offset to ensure ingestion completes first.
    Uses the isolated NLP worker when available to keep API memory usage low.
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

            # Check worker availability for logging
            worker_available = await service.check_worker_available()
            if settings.nlp_use_worker:
                if worker_available:
                    logger.info("NLP worker available, using worker for processing")
                else:
                    logger.warning("NLP worker not available, using local fallback")

            # Use worker-aware method
            result = await service.process_batch_via_worker()

            logger.info(
                "Sentiment analysis complete: processed=%d, worker_used=%s",
                result.get("processed", 0),
                result.get("worker_used", False),
            )
        except Exception as e:
            logger.error("Sentiment analysis job failed: %s", e)
        finally:
            await session.close()


async def aggregation_job() -> None:
    """Scheduled job to aggregate topic sentiment data.

    Runs 1 hour after sentiment analysis to ensure data is fresh.
    """
    logger.info("Starting scheduled topic aggregation")

    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            service = AggregationService(session)
            aggregations = await service.aggregate_topics(period_days=7, min_posts=3)

            logger.info(
                "Topic aggregation complete: topics=%d",
                len(aggregations),
            )
        except Exception as e:
            logger.error("Topic aggregation job failed: %s", e)
        finally:
            await session.close()


async def dlq_retry_job() -> None:
    """Scheduled job to retry failed posts from the dead letter queue.

    Fetches retryable posts from DLQ and attempts to reprocess them.
    Runs every hour (configurable via nlp_dlq_retry_interval_hours).
    """
    settings = get_settings()

    if not settings.nlp_enabled:
        logger.debug("NLP pipeline disabled, skipping DLQ retry")
        return

    logger.info("Starting DLQ retry job")

    try:
        dlq = await DeadLetterQueue.get_instance()
        stats = await dlq.get_stats()

        if stats["retryable"] == 0:
            logger.info("No retryable posts in DLQ")
            return

        logger.info("DLQ has %d retryable posts", stats["retryable"])

        # Get retryable posts
        failed_posts = await dlq.get_failed_posts(limit=settings.nlp_dlq_retry_batch_size)
        retryable_entries = [p for p in failed_posts if p.get("can_retry", False)]

        if not retryable_entries:
            logger.info("No posts eligible for retry")
            return

        # Get actual Post objects from database
        engine = get_engine()
        session_factory = get_session_factory(engine)

        async with session_factory() as session:
            try:
                post_ids = [entry["post_id"] for entry in retryable_entries]

                # Query posts by ID (UUIDs stored as strings in DLQ)
                stmt = select(Post).where(
                    Post.id.in_([UUID(pid) for pid in post_ids])
                )
                result = await session.execute(stmt)
                posts = list(result.scalars().all())

                if not posts:
                    logger.warning("DLQ posts not found in database, cleaning up DLQ entries")
                    for entry in retryable_entries:
                        await dlq.remove_post(entry["post_id"])
                    return

                logger.info("Retrying %d posts from DLQ", len(posts))

                # Process via NLP service
                service = NLPService(session)
                results = await service.analyze_posts_via_worker(posts)

                # Posts that succeeded are automatically removed from DLQ in analyze_posts_via_worker
                logger.info(
                    "DLQ retry complete: attempted=%d, succeeded=%d",
                    len(posts),
                    len(results),
                )

            except Exception as e:
                logger.error("DLQ retry processing failed: %s", e)
            finally:
                await session.close()

    except Exception as e:
        logger.error("DLQ retry job failed: %s", e)


def configure_scheduler(sched: AsyncIOScheduler) -> None:
    """Configure scheduler with ingestion jobs.

    Args:
        sched: The scheduler instance to configure with jobs.
    """
    settings = get_settings()

    # YouTube job (only if API key is configured)
    if settings.youtube_api_key:
        sched.add_job(
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
    sched.add_job(
        riot_ingestion_job,
        "interval",
        hours=6,
        id="riot_ingestion",
        name="OfficialNews News Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled OfficialNews ingestion job (every 6 hours)")

    # TierSite job (always enabled)
    sched.add_job(
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
        sched.add_job(
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
    sched.add_job(
        guidesite_ingestion_job,
        "interval",
        hours=6,
        id="guide-site_ingestion",
        name="GuideSite Guide Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled GuideSite ingestion job (every 6 hours)")

    # NewsSourceA job (RSS, always enabled)
    sched.add_job(
        newssource_a_ingestion_job,
        "interval",
        hours=6,
        id="news-source-a_ingestion",
        name="NewsSourceA Article Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled NewsSourceA ingestion job (every 6 hours)")

    # News Source B job (RSS, always enabled)
    sched.add_job(
        newssource_b_ingestion_job,
        "interval",
        hours=6,
        id="news-source-b_ingestion",
        name="News Source B Article Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled News Source B ingestion job (every 6 hours)")

    # Reddit job (always enabled - public JSON/RSS)
    sched.add_job(
        reddit_ingestion_job,
        "interval",
        hours=6,
        id="reddit_ingestion",
        name="Reddit Post Ingestion",
        replace_existing=True,
    )
    logger.info("Scheduled Reddit ingestion job (every 6 hours)")

    # Sentiment analysis job (configurable, runs with offset after ingestion)
    if settings.nlp_enabled:
        sched.add_job(
            sentiment_analysis_job,
            "interval",
            hours=6,
            minutes=30,  # 30min offset to run after ingestion jobs complete
            id="sentiment_analysis",
            name="Sentiment Analysis",
            replace_existing=True,
        )
        logger.info("Scheduled sentiment analysis job (every 6 hours + 30min offset)")

        # Aggregation job (runs after sentiment analysis)
        sched.add_job(
            aggregation_job,
            "interval",
            hours=6,
            minutes=45,  # 15min after sentiment analysis
            id="topic_aggregation",
            name="Topic Aggregation",
            replace_existing=True,
        )
        logger.info("Scheduled topic aggregation job (every 6 hours + 45min offset)")

        # DLQ retry job (retries failed posts from dead letter queue)
        sched.add_job(
            dlq_retry_job,
            "interval",
            hours=settings.nlp_dlq_retry_interval_hours,
            id="dlq_retry",
            name="DLQ Retry",
            replace_existing=True,
        )
        logger.info(
            "Scheduled DLQ retry job (every %d hours)",
            settings.nlp_dlq_retry_interval_hours,
        )
    else:
        logger.info("NLP pipeline disabled, skipping sentiment analysis job")


@asynccontextmanager
async def scheduler_lifespan() -> AsyncIterator[None]:
    """Async context manager for scheduler lifecycle.

    Creates and starts the APScheduler with proper event loop integration.
    Handles exceptions during startup to prevent silent failures.
    """
    sched = get_scheduler()

    try:
        # Configure jobs before starting
        configure_scheduler(sched)
        logger.info("Scheduler configured with %d jobs", len(sched.get_jobs()))

        # Start the scheduler
        sched.start()

        # Verify scheduler is actually running
        if sched.running:
            logger.info("Scheduler started successfully (running=True)")
        else:
            logger.error("Scheduler.start() called but scheduler.running is False")
            raise RuntimeError("Scheduler failed to start - running state is False")

    except Exception as e:
        logger.exception("Failed to start scheduler: %s", e)
        raise

    try:
        yield
    finally:
        try:
            sched.shutdown(wait=False)
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.warning("Error shutting down scheduler: %s", e)
