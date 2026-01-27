"""NLP service orchestration layer."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.models import Post, SentimentResult, SentimentLabel
from app.nlp.sentiment import SentimentAnalyzer, SentimentScore
from app.nlp.topics import TopicDetector, TopicResult
from app.nlp.toxicity import ToxicityDetector, ToxicityResult

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
        """Get or create sentiment analyzer."""
        if self._analyzer is None:
            self._analyzer = SentimentAnalyzer(batch_size=self.settings.nlp_batch_size)
        return self._analyzer

    def _get_topic_detector(self) -> TopicDetector:
        """Get or create topic detector."""
        if self._topic_detector is None:
            self._topic_detector = TopicDetector(batch_size=self.settings.nlp_batch_size)
        return self._topic_detector

    def _get_toxicity_detector(self) -> ToxicityDetector:
        """Get or create toxicity detector."""
        if self._toxicity_detector is None:
            self._toxicity_detector = ToxicityDetector(batch_size=self.settings.nlp_batch_size)
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

    async def analyze_posts(self, posts: list[Post]) -> list[SentimentResult]:
        """Run sentiment, topic, and toxicity analysis on posts and store results.

        Toxic posts (interpersonal attacks, threats, harassment) are deleted
        from the database rather than stored.

        Args:
            posts: Posts to analyze.

        Returns:
            List of created SentimentResult objects (non-toxic only).
        """
        if not posts:
            return []

        analyzer = self._get_analyzer()
        topic_detector = self._get_topic_detector()
        toxicity_detector = self._get_toxicity_detector()
        ttl_hours = self.settings.nlp_result_ttl_hours

        # Extract text from posts
        texts = [self._get_text_for_analysis(p) for p in posts]

        # Run batch analysis
        scores = analyzer.analyze_batch(texts)
        topic_results = topic_detector.detect_batch(texts)
        toxicity_results = toxicity_detector.detect_batch(texts)

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

            # Map label string to enum
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

    async def process_batch(self) -> dict:
        """Main entry point for batch sentiment processing.

        Fetches unprocessed posts and analyzes them.

        Returns:
            Dict with processing statistics.
        """
        posts = await self.get_unprocessed_posts()

        if not posts:
            logger.info("No posts need sentiment analysis")
            return {"processed": 0, "filtered_toxic": 0, "status": "complete"}

        logger.info("Processing %d posts for sentiment analysis", len(posts))
        initial_count = len(posts)
        results = await self.analyze_posts(posts)
        filtered_count = initial_count - len(results)

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
