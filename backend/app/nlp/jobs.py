"""NLP job management for manual trigger and status tracking."""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.nlp.valkey_store import ValkeyJobStore

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Status of an NLP job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobProgress(BaseModel):
    """Progress information for an NLP job."""

    job_id: str
    status: JobStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    posts_processed: int = 0
    posts_total: int = 0
    filtered_toxic: int = 0
    error: str | None = None


class NLPJobManager:
    """Manages NLP job state and execution.

    Uses Valkey for state persistence across restarts.
    Singleton pattern to ensure only one job runs at a time per instance.
    """

    _instance: "NLPJobManager | None" = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "NLPJobManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._current_job: JobProgress | None = None
        self._cancel_requested = False
        self._task: asyncio.Task | None = None
        self._rate_limit_seconds = 300  # 5 minutes between manual triggers
        self._store: ValkeyJobStore | None = None

    async def _get_store(self) -> ValkeyJobStore:
        """Get or create the Valkey store instance."""
        if self._store is None:
            self._store = await ValkeyJobStore.get_instance()
        return self._store

    async def _restore_state(self) -> None:
        """Restore job state from Valkey on startup."""
        try:
            store = await self._get_store()
            job_data = await store.get_job_state()

            if job_data:
                # If there was a running job, mark it as failed (process crashed)
                if job_data.get("status") == JobStatus.RUNNING:
                    job_data["status"] = JobStatus.FAILED
                    job_data["error"] = "Process restarted during execution"
                    job_data["completed_at"] = datetime.now(timezone.utc)
                    await store.set_job_state(job_data)

                self._current_job = JobProgress(**job_data)
                logger.info("Restored job state from Valkey: %s", self._current_job.job_id)
        except Exception as e:
            logger.warning("Failed to restore job state from Valkey: %s", e)

    @property
    def current_job(self) -> JobProgress | None:
        """Get current job progress."""
        return self._current_job

    @property
    def is_running(self) -> bool:
        """Check if a job is currently running."""
        return (
            self._current_job is not None
            and self._current_job.status == JobStatus.RUNNING
        )

    async def can_trigger(self) -> tuple[bool, str | None]:
        """Check if a new job can be triggered.

        Returns:
            Tuple of (can_trigger, reason_if_not).
        """
        if self.is_running:
            return False, "A job is already running"

        try:
            store = await self._get_store()
            last_trigger = await store.get_last_trigger()

            if last_trigger:
                elapsed = (datetime.now(timezone.utc) - last_trigger).total_seconds()
                if elapsed < self._rate_limit_seconds:
                    remaining = int(self._rate_limit_seconds - elapsed)
                    return False, f"Rate limited. Try again in {remaining} seconds"
        except Exception as e:
            logger.warning("Failed to check rate limit from Valkey: %s", e)
            # Fail open - allow trigger if Valkey is unavailable

        return True, None

    async def _generate_job_id(self) -> str:
        """Generate a unique job ID using Valkey counter."""
        try:
            store = await self._get_store()
            counter = await store.increment_job_counter()
        except Exception:
            # Fallback to timestamp-based ID if Valkey unavailable
            counter = int(datetime.now(timezone.utc).timestamp() * 1000) % 100000

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"nlp-{timestamp}-{counter}"

    async def _persist_job_state(self) -> None:
        """Persist current job state to Valkey."""
        if self._current_job is None:
            return

        try:
            store = await self._get_store()
            await store.set_job_state(self._current_job.model_dump())
        except Exception as e:
            logger.warning("Failed to persist job state to Valkey: %s", e)

    async def trigger_job(self) -> JobProgress:
        """Start a new NLP processing job.

        Returns:
            JobProgress with initial status.

        Raises:
            RuntimeError: If job cannot be started.
        """
        async with self._lock:
            can_start, reason = await self.can_trigger()
            if not can_start:
                raise RuntimeError(reason)

            job_id = await self._generate_job_id()
            self._current_job = JobProgress(
                job_id=job_id,
                status=JobStatus.PENDING,
            )
            self._cancel_requested = False

            # Persist initial state and last trigger time
            try:
                store = await self._get_store()
                await store.set_last_trigger(datetime.now(timezone.utc))
                await self._persist_job_state()
            except Exception as e:
                logger.warning("Failed to persist to Valkey: %s", e)

            # Start background task
            self._task = asyncio.create_task(self._run_job())

            return self._current_job

    async def _run_job(self) -> None:
        """Execute the NLP processing job.

        Uses the isolated NLP worker when available to keep API memory low.
        Falls back to local processing if worker unavailable.
        """
        if self._current_job is None:
            return

        from app.database import get_engine, get_session_factory
        from app.nlp import NLPService

        self._current_job.status = JobStatus.RUNNING
        self._current_job.started_at = datetime.now(timezone.utc)
        await self._persist_job_state()

        engine = get_engine()
        session_factory = get_session_factory(engine)

        try:
            async with session_factory() as session:
                service = NLPService(session)

                # Check worker availability
                worker_available = await service.check_worker_available()
                if worker_available:
                    logger.info("NLP worker available, using worker for processing")
                else:
                    logger.warning("NLP worker not available, using local fallback")

                # Get stats to determine total posts
                stats = await service.get_stats()
                self._current_job.posts_total = stats["needs_analysis"]
                await self._persist_job_state()

                if self._current_job.posts_total == 0:
                    self._current_job.status = JobStatus.COMPLETED
                    self._current_job.completed_at = datetime.now(timezone.utc)
                    await self._persist_job_state()
                    logger.info("NLP job completed: no posts to process")
                    return

                # Process in chunks until done or cancelled
                processed_total = 0
                filtered_total = 0

                while not self._cancel_requested:
                    posts = await service.get_unprocessed_posts()
                    if not posts:
                        break

                    # Use worker-aware method for processing
                    results = await service.analyze_posts_via_worker(posts)
                    processed_count = len(results)
                    filtered_count = len(posts) - processed_count

                    processed_total += processed_count
                    filtered_total += filtered_count

                    self._current_job.posts_processed = processed_total
                    self._current_job.filtered_toxic = filtered_total
                    await self._persist_job_state()

                    logger.info(
                        "NLP job progress: %d/%d processed",
                        processed_total,
                        self._current_job.posts_total,
                    )

                if self._cancel_requested:
                    self._current_job.status = JobStatus.CANCELLED
                    logger.info("NLP job cancelled after processing %d posts", processed_total)
                else:
                    self._current_job.status = JobStatus.COMPLETED
                    logger.info("NLP job completed: %d posts processed", processed_total)

        except Exception as e:
            logger.error("NLP job failed: %s", e)
            self._current_job.status = JobStatus.FAILED
            self._current_job.error = str(e)
        finally:
            self._current_job.completed_at = datetime.now(timezone.utc)
            await self._persist_job_state()

    async def cancel_job(self) -> bool:
        """Request cancellation of the current job.

        Returns:
            True if cancellation was requested, False if no job running.
        """
        if not self.is_running:
            return False

        self._cancel_requested = True
        logger.info("Cancellation requested for current NLP job")
        return True

    async def get_status(self) -> dict[str, Any]:
        """Get current job status.

        Returns:
            Dict with job status information.
        """
        # Try to restore state if we don't have it locally
        if self._current_job is None:
            await self._restore_state()

        can_trigger, _ = await self.can_trigger()

        if self._current_job is None:
            return {
                "has_job": False,
                "job": None,
                "can_trigger": can_trigger,
            }

        return {
            "has_job": True,
            "job": self._current_job.model_dump(),
            "can_trigger": can_trigger,
        }


# Global job manager instance
_job_manager: NLPJobManager | None = None


def get_job_manager() -> NLPJobManager:
    """Get the global NLP job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = NLPJobManager()
    return _job_manager
