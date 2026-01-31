"""NLP service orchestration layer."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.models import Post, SentimentResult, SentimentLabel
from app.nlp.sentiment import SentimentAnalyzer, SentimentScore
from app.nlp.topics import TopicDetector, TopicResult
from app.nlp.toxicity import ToxicityDetector, ToxicityResult
from app.nlp.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    get_model_breaker,
    with_retry,
)
from app.nlp.dead_letter import DeadLetterQueue

logger = logging.getLogger(__name__)


class NLPService:
    """Orchestrates NLP processing for posts.

    Handles querying unprocessed posts, running sentiment analysis,
    and storing results with TTL-based cache invalidation.
    """

    def __init__(
        self,
        session: AsyncSession,
        analyzer: SentimentAnalyzer | None = None,
        topic_detector: TopicDetector | None = None,
        toxicity_detector: ToxicityDetector | None = None,
    ):
        """Initialize NLP service.

        Args:
            session: Database session for queries.
            analyzer: Optional pre-initialized analyzer (for reuse across batches).
            topic_detector: Optional pre-initialized topic detector.
            toxicity_detector: Optional pre-initialized toxicity detector.
        """
        self.session = session
        self.settings = get_settings()
        self._analyzer = analyzer
        self._topic_detector = topic_detector
        self._toxicity_detector = toxicity_detector

    def _get_analyzer(self) -> SentimentAnalyzer:
        """Get or create sentiment analyzer with circuit breaker protection."""
        if self._analyzer is None:
            breaker = get_model_breaker("sentiment")
            try:
                self._analyzer = breaker.call(
                    SentimentAnalyzer,
                    batch_size=self.settings.nlp_batch_size,
                )
            except CircuitOpenError:
                logger.warning("Sentiment model circuit breaker is open")
                raise
            except Exception as e:
                logger.error("Failed to load sentiment model: %s", e)
                raise
        return self._analyzer

    def _get_topic_detector(self) -> TopicDetector:
        """Get or create topic detector with circuit breaker protection."""
        if self._topic_detector is None:
            breaker = get_model_breaker("topics")
            try:
                self._topic_detector = breaker.call(
                    TopicDetector,
                    batch_size=self.settings.nlp_batch_size,
                )
            except CircuitOpenError:
                logger.warning("Topic model circuit breaker is open")
                raise
            except Exception as e:
                logger.error("Failed to load topic model: %s", e)
                raise
        return self._topic_detector

    def _get_toxicity_detector(self) -> ToxicityDetector:
        """Get or create toxicity detector with circuit breaker protection."""
        if self._toxicity_detector is None:
            breaker = get_model_breaker("toxicity")
            try:
                self._toxicity_detector = breaker.call(
                    ToxicityDetector,
                    batch_size=self.settings.nlp_batch_size,
                )
            except CircuitOpenError:
                logger.warning("Toxicity model circuit breaker is open")
                raise
            except Exception as e:
                logger.error("Failed to load toxicity model: %s", e)
                raise
        return self._toxicity_detector

    async def get_unprocessed_posts(self, limit: int | None = None) -> list[Post]:
        """Get posts that need sentiment analysis.

        Returns posts where:
        - No sentiment result exists, OR
        - Sentiment result has expired (expires_at < now)

        Args:
            limit: Maximum posts to return. Defaults to nlp_chunk_size.

        Returns:
            List of Post objects needing analysis.
        """
        if limit is None:
            limit = self.settings.nlp_chunk_size

        now = datetime.now(timezone.utc)

        # Subquery to find posts with valid (non-expired) sentiment
        valid_sentiment_subq = (
            select(SentimentResult.post_id)
            .where(
                or_(
                    SentimentResult.expires_at.is_(None),
                    SentimentResult.expires_at > now,
                )
            )
            .subquery()
        )

        # Select posts NOT in valid sentiment subquery
        stmt = (
            select(Post)
            .where(Post.id.notin_(select(valid_sentiment_subq.c.post_id)))
            .order_by(Post.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _get_text_for_analysis(self, post: Post) -> str:
        """Extract text to analyze from a post.

        Prefers content, falls back to title.

        Args:
            post: Post to extract text from.

        Returns:
            Text string for sentiment analysis.
        """
        if post.content and post.content.strip():
            return post.content.strip()
        if post.title and post.title.strip():
            return post.title.strip()
        return ""

    def _analyze_batch_with_retry(
        self,
        analyzer: SentimentAnalyzer,
        topic_detector: TopicDetector,
        toxicity_detector: ToxicityDetector,
        texts: list[str],
    ) -> tuple[list[SentimentScore], list[TopicResult], list[ToxicityResult]]:
        """Run batch analysis with retry logic.

        Args:
            analyzer: Sentiment analyzer.
            topic_detector: Topic detector.
            toxicity_detector: Toxicity detector.
            texts: Texts to analyze.

        Returns:
            Tuple of (sentiment scores, topic results, toxicity results).
        """
        sentiment_breaker = get_model_breaker("sentiment")
        topic_breaker = get_model_breaker("topics")
        toxicity_breaker = get_model_breaker("toxicity")

        # Run each analysis with circuit breaker protection
        scores = sentiment_breaker.call(analyzer.analyze_batch, texts)
        topic_results = topic_breaker.call(topic_detector.detect_batch, texts)
        toxicity_results = toxicity_breaker.call(toxicity_detector.detect_batch, texts)

        return scores, topic_results, toxicity_results

    async def analyze_posts(self, posts: list[Post]) -> list[SentimentResult]:
        """Run sentiment, topic, and toxicity analysis on posts and store results.

        Toxic posts (interpersonal attacks, threats, harassment) are deleted
        from the database rather than stored.

        Uses circuit breakers and retry logic for resilience.

        Args:
            posts: Posts to analyze.

        Returns:
            List of created SentimentResult objects (non-toxic only).
        """
        if not posts:
            return []

        try:
            analyzer = self._get_analyzer()
            topic_detector = self._get_topic_detector()
            toxicity_detector = self._get_toxicity_detector()
        except CircuitOpenError as e:
            logger.error("Cannot analyze posts - circuit breaker open: %s", e)
            return []

        ttl_hours = self.settings.nlp_result_ttl_hours

        # Extract text from posts
        texts = [self._get_text_for_analysis(p) for p in posts]

        # Run batch analysis with circuit breaker protection and timeout
        timeout_seconds = self.settings.nlp_batch_timeout_seconds
        try:
            async with asyncio.timeout(timeout_seconds):
                # Run synchronous batch analysis in executor to respect timeout
                loop = asyncio.get_event_loop()
                scores, topic_results, toxicity_results = await loop.run_in_executor(
                    None,
                    self._analyze_batch_with_retry,
                    analyzer, topic_detector, toxicity_detector, texts,
                )
        except asyncio.TimeoutError:
            logger.error("Batch analysis timed out after %d seconds", timeout_seconds)
            await self.add_to_dlq(posts, f"Batch timeout after {timeout_seconds}s")
            return []
        except CircuitOpenError as e:
            logger.error("Analysis failed - circuit breaker open: %s", e)
            await self.add_to_dlq(posts, f"Circuit breaker open: {e}")
            return []
        except Exception as e:
            logger.error("Analysis failed: %s", e)
            await self.add_to_dlq(posts, f"Analysis error: {e}")
            return []

        # Create result objects
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        results: list[SentimentResult] = []
        toxic_posts: list[Post] = []

        for post, score, topic_result, toxicity_result in zip(
            posts, scores, topic_results, toxicity_results
        ):
            # Filter out toxic posts - delete them instead of storing
            if toxicity_result.is_toxic:
                toxic_posts.append(post)
                continue

            # Map label string to enum (score.label is lowercase: "positive", "neutral", "negative")
            label = SentimentLabel(score.label)

            result = SentimentResult(
                post_id=post.id,
                label=label,
                confidence=score.confidence,
                scores=score.scores,
                topics=topic_result.to_json(),
                is_toxic=False,
                toxicity_score=toxicity_result.toxicity_score,
                model_name=analyzer.model_name,
                analyzed_at=now,
                expires_at=expires_at,
            )
            self.session.add(result)
            results.append(result)

        # Delete toxic posts from database
        for post in toxic_posts:
            await self.session.delete(post)

        await self.session.commit()

        if toxic_posts:
            logger.info("Filtered out %d toxic posts", len(toxic_posts))
        logger.info("Stored %d sentiment results", len(results))

        return results

    async def process_batch(self) -> dict[str, Any]:
        """Main entry point for batch sentiment processing.

        Fetches unprocessed posts and analyzes them.
        Handles circuit breaker failures gracefully.

        Returns:
            Dict with processing statistics.
        """
        posts = await self.get_unprocessed_posts()

        if not posts:
            logger.info("No posts need sentiment analysis")
            return {"processed": 0, "filtered_toxic": 0, "status": "complete"}

        logger.info("Processing %d posts for sentiment analysis", len(posts))
        initial_count = len(posts)

        try:
            results = await self.analyze_posts(posts)
        except CircuitOpenError as e:
            logger.error("Processing failed - circuit breaker open: %s", e)
            return {
                "processed": 0,
                "filtered_toxic": 0,
                "status": "failed",
                "error": "Service temporarily unavailable - circuit breaker open",
            }

        filtered_count = initial_count - len(results)

        # Check if we got no results due to failures
        if len(results) == 0 and initial_count > 0:
            return {
                "processed": 0,
                "filtered_toxic": filtered_count,
                "status": "partial",
                "warning": "Analysis returned no results - possible model failure",
            }

        return {
            "processed": len(results),
            "filtered_toxic": filtered_count,
            "status": "complete",
        }

    async def get_stats(self) -> dict:
        """Get NLP processing statistics.

        Returns:
            Dict with total posts, analyzed counts, etc.
        """
        now = datetime.now(timezone.utc)

        # Total posts
        total_result = await self.session.execute(select(func.count(Post.id)))
        total_posts = total_result.scalar() or 0

        # Posts with valid (non-expired) sentiment
        valid_sentiment_stmt = select(func.count(SentimentResult.id)).where(
            or_(
                SentimentResult.expires_at.is_(None),
                SentimentResult.expires_at > now,
            )
        )
        valid_result = await self.session.execute(valid_sentiment_stmt)
        with_sentiment = valid_result.scalar() or 0

        # Posts needing analysis
        needs_analysis = total_posts - with_sentiment

        return {
            "total_posts": total_posts,
            "with_valid_sentiment": with_sentiment,
            "needs_analysis": needs_analysis,
            "config": {
                "batch_size": self.settings.nlp_batch_size,
                "chunk_size": self.settings.nlp_chunk_size,
                "ttl_hours": self.settings.nlp_result_ttl_hours,
                "enabled": self.settings.nlp_enabled,
            },
        }

    async def add_to_dlq(
        self,
        posts: list[Post],
        error: str,
    ) -> int:
        """Add failed posts to the dead letter queue.

        Args:
            posts: Posts that failed processing.
            error: Error message describing the failure.

        Returns:
            Number of posts added to DLQ.
        """
        if not posts:
            return 0

        try:
            dlq = await DeadLetterQueue.get_instance()
            count = 0

            for post in posts:
                content = self._get_text_for_analysis(post)
                await dlq.add_failed_post(
                    post_id=str(post.id),
                    error=error,
                    post_content=content,
                )
                count += 1

            logger.info("Added %d posts to DLQ: %s", count, error)
            return count
        except Exception as e:
            logger.warning("Failed to add posts to DLQ: %s", e)
            return 0

    async def remove_from_dlq(self, post_id: str) -> bool:
        """Remove a post from the dead letter queue after successful processing.

        Args:
            post_id: Post identifier.

        Returns:
            True if removed, False otherwise.
        """
        try:
            dlq = await DeadLetterQueue.get_instance()
            return await dlq.remove_post(post_id)
        except Exception as e:
            logger.warning("Failed to remove post from DLQ: %s", e)
            return False

    async def should_process_post(self, post_id: str) -> bool:
        """Check if a post should be processed (not exhausted in DLQ).

        Args:
            post_id: Post identifier.

        Returns:
            True if post should be processed.
        """
        try:
            dlq = await DeadLetterQueue.get_instance()
            return await dlq.should_retry(post_id)
        except Exception as e:
            logger.warning("Failed to check DLQ status: %s", e)
            return True  # Fail open

    async def check_worker_available(self) -> bool:
        """Check if the NLP worker is available and ready.

        Returns:
            True if worker is available, False otherwise.
        """
        if not self.settings.nlp_use_worker:
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.settings.nlp_worker_url}/ready")
                return response.status_code == 200
        except Exception as e:
            logger.debug("Worker not available: %s", e)
            return False

    async def _call_worker(
        self,
        texts: list[str],
    ) -> dict[str, Any] | None:
        """Call the NLP worker for batch analysis.

        Args:
            texts: Texts to analyze.

        Returns:
            Worker response with sentiment, topics, toxicity or None on error.
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.nlp_worker_url}/analyze",
                    json={"texts": texts},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Worker returned error: %s", e.response.status_code)
            return None
        except Exception as e:
            logger.error("Worker call failed: %s", e)
            return None

    async def analyze_posts_via_worker(
        self,
        posts: list[Post],
    ) -> list[SentimentResult]:
        """Analyze posts using the isolated NLP worker.

        Falls back to local processing if worker unavailable.
        Adds failed posts to DLQ.

        Args:
            posts: Posts to analyze.

        Returns:
            List of created SentimentResult objects.
        """
        if not posts:
            return []

        # Check worker availability
        worker_available = await self.check_worker_available()

        if not worker_available:
            logger.warning("Worker unavailable, falling back to local processing")
            return await self.analyze_posts(posts)

        # Extract texts
        texts = [self._get_text_for_analysis(p) for p in posts]

        # Call worker
        logger.info("Sending %d posts to NLP worker", len(posts))
        worker_response = await self._call_worker(texts)

        if worker_response is None:
            # Worker failed - add to DLQ and fallback
            await self.add_to_dlq(posts, "Worker call failed")
            logger.warning("Worker failed, falling back to local processing")
            return await self.analyze_posts(posts)

        # Process worker response
        ttl_hours = self.settings.nlp_result_ttl_hours
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        results: list[SentimentResult] = []
        toxic_posts: list[Post] = []

        sentiment_results = worker_response.get("sentiment", [])
        topic_results = worker_response.get("topics", [])
        toxicity_results = worker_response.get("toxicity", [])

        for i, post in enumerate(posts):
            if i >= len(sentiment_results):
                # Partial response - add remaining to DLQ
                await self.add_to_dlq([post], "Partial worker response")
                continue

            sentiment = sentiment_results[i]
            topics = topic_results[i] if i < len(topic_results) else {}
            toxicity = toxicity_results[i] if i < len(toxicity_results) else {}

            # Filter out toxic posts
            if toxicity.get("is_toxic", False):
                toxic_posts.append(post)
                continue

            # Create result
            try:
                label = SentimentLabel(sentiment["label"])
                result = SentimentResult(
                    post_id=post.id,
                    label=label,
                    confidence=sentiment["confidence"],
                    scores=sentiment.get("scores", {}),
                    topics=topics,
                    is_toxic=False,
                    toxicity_score=toxicity.get("toxicity_score", 0.0),
                    model_name="worker",
                    analyzed_at=now,
                    expires_at=expires_at,
                )
                self.session.add(result)
                results.append(result)

                # Remove from DLQ on success
                await self.remove_from_dlq(str(post.id))

            except Exception as e:
                logger.error("Failed to create result for post %s: %s", post.id, e)
                await self.add_to_dlq([post], str(e))

        # Delete toxic posts
        for post in toxic_posts:
            await self.session.delete(post)

        await self.session.commit()

        if toxic_posts:
            logger.info("Filtered out %d toxic posts via worker", len(toxic_posts))
        logger.info("Stored %d sentiment results via worker", len(results))

        return results

    async def process_batch_via_worker(self) -> dict[str, Any]:
        """Process batch using the NLP worker.

        Fetches unprocessed posts and analyzes them via worker.
        Falls back to local processing if worker unavailable.

        Returns:
            Dict with processing statistics.
        """
        # Check worker first
        worker_available = await self.check_worker_available()
        if not worker_available and self.settings.nlp_use_worker:
            logger.warning("NLP worker not available, will use local fallback")

        posts = await self.get_unprocessed_posts()

        if not posts:
            logger.info("No posts need sentiment analysis")
            return {
                "processed": 0,
                "filtered_toxic": 0,
                "status": "complete",
                "worker_used": False,
            }

        logger.info("Processing %d posts for sentiment analysis", len(posts))
        initial_count = len(posts)

        try:
            if worker_available:
                results = await self.analyze_posts_via_worker(posts)
            else:
                results = await self.analyze_posts(posts)
        except CircuitOpenError as e:
            logger.error("Processing failed - circuit breaker open: %s", e)
            await self.add_to_dlq(posts, f"Circuit breaker open: {e}")
            return {
                "processed": 0,
                "filtered_toxic": 0,
                "status": "failed",
                "error": "Service temporarily unavailable - circuit breaker open",
                "worker_used": worker_available,
            }
        except Exception as e:
            logger.error("Processing failed: %s", e)
            await self.add_to_dlq(posts, str(e))
            return {
                "processed": 0,
                "filtered_toxic": 0,
                "status": "failed",
                "error": str(e),
                "worker_used": worker_available,
            }

        filtered_count = initial_count - len(results)

        return {
            "processed": len(results),
            "filtered_toxic": filtered_count,
            "status": "complete",
            "worker_used": worker_available,
        }
