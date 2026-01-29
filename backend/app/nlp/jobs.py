"""NLP job management for manual trigger and status tracking."""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

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

    Singleton pattern to ensure only one job runs at a time.
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
        self._job_counter = 0
        self._cancel_requested = False
        self._task: asyncio.Task | None = None
        self._last_trigger: datetime | None = None
        self._rate_limit_seconds = 300  # 5 minutes between manual triggers

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

    def can_trigger(self) -> tuple[bool, str | None]:
        """Check if a new job can be triggered.

        Returns:
            Tuple of (can_trigger, reason_if_not).
        """
        if self.is_running:
            return False, "A job is already running"

        if self._last_trigger:
            elapsed = (datetime.now(timezone.utc) - self._last_trigger).total_seconds()
            if elapsed < self._rate_limit_seconds:
                remaining = int(self._rate_limit_seconds - elapsed)
                return False, f"Rate limited. Try again in {remaining} seconds"

        return True, None

    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        self._job_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"nlp-{timestamp}-{self._job_counter}"

    async def trigger_job(self) -> JobProgress:
        """Start a new NLP processing job.

        Returns:
            JobProgress with initial status.

        Raises:
            RuntimeError: If job cannot be started.
        """
        async with self._lock:
            can_start, reason = self.can_trigger()
            if not can_start:
                raise RuntimeError(reason)

            job_id = self._generate_job_id()
            self._current_job = JobProgress(
                job_id=job_id,
                status=JobStatus.PENDING,
            )
            self._cancel_requested = False
            self._last_trigger = datetime.now(timezone.utc)

            # Start background task
            self._task = asyncio.create_task(self._run_job())

            return self._current_job

    async def _run_job(self) -> None:
        """Execute the NLP processing job."""
        if self._current_job is None:
            return

        from app.database import get_engine, get_session_factory
        from app.nlp import NLPService

        self._current_job.status = JobStatus.RUNNING
        self._current_job.started_at = datetime.now(timezone.utc)

        engine = get_engine()
        session_factory = get_session_factory(engine)

        try:
            async with session_factory() as session:
                service = NLPService(session)

                # Get stats to determine total posts
                stats = await service.get_stats()
                self._current_job.posts_total = stats["needs_analysis"]

                if self._current_job.posts_total == 0:
                    self._current_job.status = JobStatus.COMPLETED
                    self._current_job.completed_at = datetime.now(timezone.utc)
                    logger.info("NLP job completed: no posts to process")
                    return

                # Process in chunks until done or cancelled
                processed_total = 0
                filtered_total = 0

                while not self._cancel_requested:
                    posts = await service.get_unprocessed_posts()
                    if not posts:
                        break

                    results = await service.analyze_posts(posts)
                    processed_count = len(results)
                    filtered_count = len(posts) - processed_count

                    processed_total += processed_count
                    filtered_total += filtered_count

                    self._current_job.posts_processed = processed_total
                    self._current_job.filtered_toxic = filtered_total

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

    def get_status(self) -> dict[str, Any]:
        """Get current job status.

        Returns:
            Dict with job status information.
        """
        if self._current_job is None:
            return {
                "has_job": False,
                "job": None,
                "can_trigger": self.can_trigger()[0],
            }

        return {
            "has_job": True,
            "job": self._current_job.model_dump(),
            "can_trigger": self.can_trigger()[0],
        }


# Global job manager instance
_job_manager: NLPJobManager | None = None


def get_job_manager() -> NLPJobManager:
    """Get the global NLP job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = NLPJobManager()
    return _job_manager
