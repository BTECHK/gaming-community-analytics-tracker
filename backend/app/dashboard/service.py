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
    ) -> tuple[list[dict], str | None]:
        """Get trending topics with sentiment data.

        Args:
            themes: Optional list of theme names to filter by.
            platforms: Optional list of platform names to filter by (topics must have posts from these platforms).
            period_days: Only include aggregations with period_end within this many days.
            limit: Maximum topics to return.

        Returns:
            Tuple of (topic data dicts, last_updated ISO string or None).
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

        # Compute last_updated as max updated_at across returned aggregations
        last_updated: str | None = None
        if aggregations:
            max_updated = max(agg.updated_at for agg in aggregations)
            last_updated = max_updated.isoformat() if max_updated else None

        # Build topic dicts with velocity data
        topics = []
        for agg in aggregations:
            topic_dict = self._aggregation_to_dict(agg)
            try:
                velocity = await self.get_topic_velocity(agg.topic_slug, period_days)
            except Exception:
                velocity = {"velocity_label": None, "velocity_pct": 0.0}
            topic_dict["velocity_label"] = velocity["velocity_label"]
            topic_dict["velocity_pct"] = velocity["velocity_pct"]
            topics.append(topic_dict)

        return topics, last_updated

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

    async def get_topic_velocity(
        self, topic_slug: str, period_days: int = 7
    ) -> dict:
        """Calculate topic velocity by comparing current vs previous period.

        Args:
            topic_slug: Slug of the topic to check.
            period_days: Length of each comparison window in days.

        Returns:
            Dict with velocity_label ('rising'|'steady'|'cooling'|None) and velocity_pct (float).
        """
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=period_days)
        previous_start = current_start - timedelta(days=period_days)

        # Get current aggregation post_count
        agg_stmt = select(Aggregation).where(Aggregation.topic_slug == topic_slug)
        agg_result = await self.session.execute(agg_stmt)
        aggregation = agg_result.scalar_one_or_none()

        if not aggregation:
            return {"velocity_label": None, "velocity_pct": 0.0}

        current_count = aggregation.post_count

        # Count posts in previous period that mention this topic
        prev_stmt = (
            select(func.count(Post.id))
            .join(SentimentResult, SentimentResult.post_id == Post.id)
            .where(
                and_(
                    Post.created_at >= previous_start,
                    Post.created_at < current_start,
                )
            )
        )
        prev_result = await self.session.execute(prev_stmt)
        previous_count = prev_result.scalar() or 0

        if previous_count == 0:
            if current_count > 0:
                return {"velocity_label": "rising", "velocity_pct": 100.0}
            return {"velocity_label": None, "velocity_pct": 0.0}

        pct_change = ((current_count - previous_count) / previous_count) * 100

        if pct_change > 20:
            label = "rising"
        elif pct_change < -20:
            label = "cooling"
        else:
            label = "steady"

        return {"velocity_label": label, "velocity_pct": round(pct_change, 1)}

    async def calculate_pulse_score(self) -> dict:
        """Calculate Community Pulse Score (0-100).

        Formula: sentiment_health (40%) + topic_diversity (30%) + volume_health (30%).

        Returns:
            Dict with pulse_score, label, and breakdown.
        """
        # Get recent aggregations
        stmt = select(Aggregation).order_by(Aggregation.post_count.desc())
        result = await self.session.execute(stmt)
        aggregations = list(result.scalars().all())

        if not aggregations:
            return {
                "pulse_score": 0,
                "label": "Critical",
                "breakdown": {
                    "sentiment_health": {"score": 0, "weight": 0.4},
                    "topic_diversity": {"score": 0, "weight": 0.3},
                    "volume_health": {"score": 0, "weight": 0.3},
                },
            }

        # sentiment_health: average positive sentiment % scaled to 0-100
        avg_positive = sum(a.sentiment_positive for a in aggregations) / len(aggregations)
        sentiment_health = min(avg_positive, 100.0)

        # topic_diversity: min(active_topic_count / 5, 1.0) * 100
        topic_diversity = min(len(aggregations) / 5.0, 1.0) * 100

        # volume_health: min(total_recent_posts / 50, 1.0) * 100
        total_posts = sum(a.post_count for a in aggregations)
        volume_health = min(total_posts / 50.0, 1.0) * 100

        pulse_score = round(
            sentiment_health * 0.4 + topic_diversity * 0.3 + volume_health * 0.3
        )

        if pulse_score <= 33:
            label = "Critical"
        elif pulse_score <= 66:
            label = "Mixed"
        else:
            label = "Healthy"

        return {
            "pulse_score": pulse_score,
            "label": label,
            "breakdown": {
                "sentiment_health": {"score": round(sentiment_health, 1), "weight": 0.4},
                "topic_diversity": {"score": round(topic_diversity, 1), "weight": 0.3},
                "volume_health": {"score": round(volume_health, 1), "weight": 0.3},
            },
        }

    async def get_stats(self) -> dict:
        """Get stats summary for dashboard banner.

        Returns:
            Dict with posts_analyzed, active_topics, sources_active, pulse_score, pulse_label.
        """
        # posts_analyzed: count of posts that have sentiment results
        posts_stmt = (
            select(func.count(Post.id))
            .join(SentimentResult, SentimentResult.post_id == Post.id)
        )
        posts_result = await self.session.execute(posts_stmt)
        posts_analyzed = posts_result.scalar() or 0

        # active_topics: count of aggregations
        topics_stmt = select(func.count(Aggregation.id))
        topics_result = await self.session.execute(topics_stmt)
        active_topics = topics_result.scalar() or 0

        # sources_active: count of distinct platforms in posts
        sources_stmt = select(func.count(func.distinct(Post.platform)))
        sources_result = await self.session.execute(sources_stmt)
        sources_active = sources_result.scalar() or 0

        # Reuse pulse score
        pulse = await self.calculate_pulse_score()

        return {
            "posts_analyzed": posts_analyzed,
            "active_topics": active_topics,
            "sources_active": sources_active,
            "pulse_score": pulse["pulse_score"],
            "pulse_label": pulse["label"],
        }

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

    async def get_sentiment_history(
        self, period_days: int = 30, granularity: str = "daily"
    ) -> list[dict]:
        """Get time-series sentiment data for charts.

        Args:
            period_days: Number of days to look back.
            granularity: 'daily' or 'weekly' bucketing.

        Returns:
            List of dicts with date, positive, neutral, negative, post_count.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

        stmt = (
            select(
                func.date_trunc(
                    "week" if granularity == "weekly" else "day",
                    Post.created_at,
                ).label("bucket"),
                func.count(Post.id).label("post_count"),
            )
            .join(SentimentResult, SentimentResult.post_id == Post.id)
            .where(Post.created_at >= cutoff)
            .group_by("bucket")
            .order_by("bucket")
        )
        result = await self.session.execute(stmt)
        buckets = result.all()

        if not buckets:
            return []

        # For each bucket, get sentiment breakdown
        history = []
        for bucket in buckets:
            bucket_date = bucket.bucket
            bucket_end = bucket_date + timedelta(days=7 if granularity == "weekly" else 1)

            sent_stmt = (
                select(
                    SentimentResult.label,
                    func.count(SentimentResult.id).label("cnt"),
                )
                .join(Post, Post.id == SentimentResult.post_id)
                .where(
                    and_(
                        Post.created_at >= bucket_date,
                        Post.created_at < bucket_end,
                    )
                )
                .group_by(SentimentResult.label)
            )
            sent_result = await self.session.execute(sent_stmt)
            sent_rows = sent_result.all()

            total = sum(r.cnt for r in sent_rows)
            counts = {r.label.value if hasattr(r.label, "value") else r.label: r.cnt for r in sent_rows}

            history.append({
                "date": bucket_date.isoformat(),
                "positive": round(counts.get("positive", 0) / total * 100, 1) if total else 0,
                "neutral": round(counts.get("neutral", 0) / total * 100, 1) if total else 0,
                "negative": round(counts.get("negative", 0) / total * 100, 1) if total else 0,
                "post_count": bucket.post_count,
            })

        return history

    async def get_activity_patterns(self, period_days: int = 30) -> dict:
        """Get hourly/daily activity distribution for heatmap.

        Args:
            period_days: Number of days to look back.

        Returns:
            Dict with heatmap (7x24 matrix) and total_posts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

        stmt = (
            select(
                func.extract("dow", Post.created_at).label("dow"),
                func.extract("hour", Post.created_at).label("hour"),
                func.count(Post.id).label("cnt"),
            )
            .where(Post.created_at >= cutoff)
            .group_by("dow", "hour")
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        # Initialize 7x24 zero matrix (Mon=0 through Sun=6)
        heatmap = [[0] * 24 for _ in range(7)]
        total_posts = 0

        for row in rows:
            # PostgreSQL dow: 0=Sunday, 1=Monday, ..., 6=Saturday
            # Convert to Mon=0: (dow + 6) % 7
            day_idx = (int(row.dow) + 6) % 7
            hour_idx = int(row.hour)
            heatmap[day_idx][hour_idx] = row.cnt
            total_posts += row.cnt

        return {"heatmap": heatmap, "total_posts": total_posts}

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
