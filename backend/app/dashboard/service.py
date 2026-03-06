"""Aggregation service for dashboard data."""

import logging
import re
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, SentimentResult, SentimentLabel, Aggregation, Platform
from app.dashboard.explanation_generator import (
    generate_sentiment_explanation,
    generate_confidence_breakdown,
)

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


class AggregationService:
    """Service for aggregating sentiment data by topic.

    Creates pre-computed aggregations for fast dashboard queries.
    """

    def __init__(self, session: AsyncSession):
        """Initialize aggregation service.

        Args:
            session: Database session for queries.
        """
        self.session = session

    async def aggregate_topics(
        self,
        period_days: int = 7,
        min_posts: int = 3,
    ) -> list[Aggregation]:
        """Aggregate sentiment by detected topics.

        Groups posts by their detected topics, calculates sentiment
        distribution, and stores representative quotes.

        Args:
            period_days: Number of days to look back.
            min_posts: Minimum posts required for a topic to be included.

        Returns:
            List of created/updated Aggregation objects.
        """
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=period_days)

        # Get current patch version
        from app.dashboard.patch_service import PatchService
        patch_service = PatchService()
        current_patch = await patch_service.get_current_patch()

        # Query posts with sentiment results
        stmt = (
            select(Post, SentimentResult)
            .join(SentimentResult, SentimentResult.post_id == Post.id)
            .where(
                and_(
                    Post.created_at >= period_start,
                    or_(
                        SentimentResult.expires_at.is_(None),
                        SentimentResult.expires_at > now,
                    ),
                )
            )
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            logger.info("No posts with sentiment data to aggregate")
            return []

        # Group by topic
        topic_data: dict[str, dict] = defaultdict(
            lambda: {
                "posts": [],
                "sentiments": {"positive": 0, "neutral": 0, "negative": 0},
                "sources": defaultdict(int),
                "quotes": [],
            }
        )

        for post, sentiment in rows:
            topics = sentiment.topics or []
            if not topics:
                continue

            for topic in topics:
                topic_name = topic.get("topic", "") if isinstance(topic, dict) else str(topic)
                if not topic_name:
                    continue

                data = topic_data[topic_name]
                data["posts"].append((post, sentiment))
                data["sentiments"][sentiment.label.value] += 1
                data["sources"][post.platform.value] += 1

                # Collect potential quotes (high confidence, with content)
                if sentiment.confidence >= 0.7 and post.content:
                    quote_text = post.content[:300]
                    if len(post.content) > 300:
                        quote_text += "..."
                    data["quotes"].append({
                        "text": quote_text,
                        "source_url": post.url,
                        "platform": post.platform.value,
                        "sentiment": sentiment.label.value,
                        "confidence": sentiment.confidence,
                    })

        # Create/update aggregations
        aggregations = []
        for topic_name, data in topic_data.items():
            post_count = len(data["posts"])
            if post_count < min_posts:
                continue

            # Calculate sentiment percentages
            total = sum(data["sentiments"].values())
            sentiment_positive = (data["sentiments"]["positive"] / total * 100) if total else 0
            sentiment_neutral = (data["sentiments"]["neutral"] / total * 100) if total else 0
            sentiment_negative = (data["sentiments"]["negative"] / total * 100) if total else 0

            # Sort quotes by confidence and select top 5
            sorted_quotes = sorted(data["quotes"], key=lambda x: x["confidence"], reverse=True)
            representative_quotes = sorted_quotes[:5]

            # Calculate confidence score (average of post confidences)
            confidences = [s.confidence for _, s in data["posts"]]
            confidence_score = sum(confidences) / len(confidences) if confidences else 0

            slug = slugify(topic_name)

            # Generate explanations
            sentiment_explanation = generate_sentiment_explanation(
                sentiment_positive=sentiment_positive,
                sentiment_neutral=sentiment_neutral,
                sentiment_negative=sentiment_negative,
                source_mix=dict(data["sources"]),
                quotes=representative_quotes,
                post_count=post_count,
            )

            confidence_breakdown = generate_confidence_breakdown(
                post_count=post_count,
                source_mix=dict(data["sources"]),
                quotes=representative_quotes,
                sentiment_positive=sentiment_positive,
                sentiment_neutral=sentiment_neutral,
                sentiment_negative=sentiment_negative,
            )

            # Check if aggregation exists
            existing = await self.session.execute(
                select(Aggregation).where(Aggregation.topic_slug == slug)
            )
            aggregation = existing.scalar_one_or_none()

            if aggregation:
                # Update existing
                aggregation.topic_name = topic_name
                aggregation.sentiment_positive = sentiment_positive
                aggregation.sentiment_neutral = sentiment_neutral
                aggregation.sentiment_negative = sentiment_negative
                aggregation.post_count = post_count
                aggregation.source_mix = dict(data["sources"])
                aggregation.representative_quotes = representative_quotes
                aggregation.period_start = period_start
                aggregation.period_end = now
                aggregation.confidence_score = confidence_score
                aggregation.patch_version = current_patch
                aggregation.sentiment_explanation = sentiment_explanation
                aggregation.confidence_breakdown = confidence_breakdown
            else:
                # Create new
                aggregation = Aggregation(
                    topic_name=topic_name,
                    topic_slug=slug,
                    sentiment_positive=sentiment_positive,
                    sentiment_neutral=sentiment_neutral,
                    sentiment_negative=sentiment_negative,
                    post_count=post_count,
                    source_mix=dict(data["sources"]),
                    representative_quotes=representative_quotes,
                    period_start=period_start,
                    period_end=now,
                    confidence_score=confidence_score,
                    patch_version=current_patch,
                    sentiment_explanation=sentiment_explanation,
                    confidence_breakdown=confidence_breakdown,
                )
                self.session.add(aggregation)

            aggregations.append(aggregation)

        await self.session.commit()
        logger.info("Created/updated %d topic aggregations", len(aggregations))
        return aggregations

    async def get_trending(
        self,
        themes: list[str] | None = None,
        platforms: list[str] | None = None,
        period_days: int = 7,
        limit: int = 10,
    ) -> list[dict]:
        """Get trending topics with sentiment data.

        Args:
            themes: Optional list of theme names to filter by.
            platforms: Optional list of platform names to filter by (topics must have posts from these platforms).
            period_days: Only include aggregations with period_end within this many days.
            limit: Maximum topics to return.

        Returns:
            List of topic data dicts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        stmt = (
            select(Aggregation)
            .where(Aggregation.period_end >= cutoff)
            .order_by(Aggregation.post_count.desc())
        )

        if themes:
            # Filter by themes (case-insensitive partial match)
            theme_filters = []
            for theme in themes:
                theme_filters.append(Aggregation.topic_name.ilike(f"%{theme}%"))
            stmt = stmt.where(or_(*theme_filters))

        # If filtering by platforms, we need to fetch more and filter in Python
        # since source_mix is a JSON column
        if platforms:
            stmt = stmt.limit(limit * 3)  # Fetch extra to account for filtering
        else:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        aggregations = result.scalars().all()

        # Filter by platforms if specified
        if platforms:
            platform_set = set(p.lower() for p in platforms)
            aggregations = [
                agg for agg in aggregations
                if agg.source_mix and any(
                    src.lower() in platform_set for src in agg.source_mix.keys()
                )
            ][:limit]

        return [self._aggregation_to_dict(agg) for agg in aggregations]

    async def get_topic_by_slug(self, slug: str) -> dict | None:
        """Get a single topic by slug.

        Args:
            slug: URL-safe topic slug.

        Returns:
            Topic data dict or None if not found.
        """
        stmt = select(Aggregation).where(Aggregation.topic_slug == slug)
        result = await self.session.execute(stmt)
        aggregation = result.scalar_one_or_none()

        if not aggregation:
            return None

        return self._aggregation_to_dict(aggregation)

    async def get_all_topics(self) -> list[dict]:
        """Get all topics for sidebar navigation.

        Returns:
            List of minimal topic info dicts.
        """
        stmt = (
            select(Aggregation)
            .order_by(Aggregation.post_count.desc())
        )
        result = await self.session.execute(stmt)
        aggregations = result.scalars().all()

        return [
            {
                "slug": agg.topic_slug,
                "name": agg.topic_name,
                "post_count": agg.post_count,
            }
            for agg in aggregations
        ]

    async def get_source_distribution(self) -> dict[str, int]:
        """Get overall source distribution across all posts.

        Returns:
            Dict mapping platform names to post counts.
        """
        stmt = select(
            Post.platform,
            func.count(Post.id).label("count"),
        ).group_by(Post.platform)

        result = await self.session.execute(stmt)
        rows = result.all()

        return {row.platform.value: row.count for row in rows}

    async def get_patch_pulse(
        self,
        patch_version: str,
        limit: int = 10,
    ) -> dict:
        """Get patch-specific sentiment data.

        Args:
            patch_version: Patch version to filter by (e.g., "16.2").
            limit: Maximum topics to return.

        Returns:
            Dict with topics, overall_sentiment, and total_posts.
        """
        # Query aggregations for this patch
        stmt = (
            select(Aggregation)
            .where(Aggregation.patch_version == patch_version)
            .order_by(Aggregation.post_count.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        aggregations = list(result.scalars().all())

        # No fallback - if no patch-specific data, return empty with message
        # This differentiates Patch Pulse from the general trending page
        if not aggregations:
            return {
                "topics": [],
                "overall_sentiment": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                },
                "total_posts": 0,
                "message": f"No community discussions found for patch {patch_version} yet. Check back soon!",
            }

        topics = [self._aggregation_to_dict(agg) for agg in aggregations]

        # Calculate overall sentiment (weighted by post count)
        total_posts = sum(agg.post_count for agg in aggregations)
        if total_posts > 0:
            weighted_positive = sum(
                agg.sentiment_positive * agg.post_count for agg in aggregations
            ) / total_posts
            weighted_neutral = sum(
                agg.sentiment_neutral * agg.post_count for agg in aggregations
            ) / total_posts
            weighted_negative = sum(
                agg.sentiment_negative * agg.post_count for agg in aggregations
            ) / total_posts
        else:
            weighted_positive = weighted_neutral = weighted_negative = 0

        return {
            "topics": topics,
            "overall_sentiment": {
                "positive": round(weighted_positive, 1),
                "neutral": round(weighted_neutral, 1),
                "negative": round(weighted_negative, 1),
            },
            "total_posts": total_posts,
        }

    def _aggregation_to_dict(self, agg: Aggregation) -> dict:
        """Convert Aggregation model to API response dict.

        Args:
            agg: Aggregation model instance.

        Returns:
            Dict suitable for JSON serialization.
        """
        return {
            "slug": agg.topic_slug,
            "name": agg.topic_name,
            "sentiment": {
                "positive": round(agg.sentiment_positive, 1),
                "neutral": round(agg.sentiment_neutral, 1),
                "negative": round(agg.sentiment_negative, 1),
            },
            "post_count": agg.post_count,
            "source_mix": agg.source_mix or {},
            "quotes": agg.representative_quotes or [],
            "confidence": round(agg.confidence_score, 2) if agg.confidence_score else None,
            "period": {
                "start": agg.period_start.isoformat() if agg.period_start else None,
                "end": agg.period_end.isoformat() if agg.period_end else None,
            },
            "summary": agg.summary,
            "sentiment_explanation": agg.sentiment_explanation,
            "confidence_breakdown": agg.confidence_breakdown,
        }
