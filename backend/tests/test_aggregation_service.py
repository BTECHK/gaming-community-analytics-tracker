"""Tests for AggregationService — aggregate_topics, velocity, empty handling."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, Platform, SentimentResult, SentimentLabel, Aggregation
from app.dashboard.service import AggregationService, slugify


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_post_with_sentiment(
    session: AsyncSession,
    title: str = "Test",
    content: str = "Content",
    platform: Platform = Platform.REDDIT,
    label: SentimentLabel = SentimentLabel.positive,
    confidence: float = 0.85,
    topics: list | None = None,
) -> tuple[Post, SentimentResult]:
    """Create and add a Post + SentimentResult pair."""
    now = datetime.now(timezone.utc)
    post = Post(
        id=str(uuid4()),
        platform=platform,
        external_id=str(uuid4()),
        title=title,
        content=content,
        author="tester",
        url="https://example.com/post",
        upvotes=5,
        comments_count=2,
        published_at=now,
        fetched_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(post)

    sr = SentimentResult(
        post_id=post.id,
        label=label,
        confidence=confidence,
        scores={label.value: confidence},
        topics=topics or ["test-topic"],
        is_toxic=False,
        toxicity_score=0.05,
        model_name="test-model",
        analyzed_at=now,
        expires_at=now + timedelta(hours=48),
    )
    session.add(sr)
    return post, sr


# ---------------------------------------------------------------------------
# aggregate_topics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aggregate_topics_creates_aggregation(test_session: AsyncSession):
    """aggregate_topics groups posts by topic and creates Aggregation rows."""
    # Insert 4 posts all with topic "balance"
    for i in range(4):
        _insert_post_with_sentiment(
            test_session,
            title=f"Balance post {i}",
            content=f"Balance discussion {i}",
            platform=Platform.REDDIT if i < 2 else Platform.YOUTUBE,
            label=SentimentLabel.positive if i % 2 == 0 else SentimentLabel.negative,
            topics=["balance"],
        )
    await test_session.commit()

    with patch("app.dashboard.patch_service.PatchService") as MockPS:
        mock_ps = MagicMock()
        mock_ps.get_current_patch = AsyncMock(return_value="16.2")
        MockPS.return_value = mock_ps

        svc = AggregationService(test_session)
        aggs = await svc.aggregate_topics(period_days=7, min_posts=3)

    assert len(aggs) >= 1
    balance = next((a for a in aggs if a.topic_slug == "balance"), None)
    assert balance is not None
    assert balance.post_count == 4
    assert balance.sentiment_positive == 50.0
    assert balance.sentiment_negative == 50.0
    assert balance.source_mix is not None
    assert "reddit" in balance.source_mix
    assert "youtube" in balance.source_mix


@pytest.mark.asyncio
async def test_aggregate_topics_respects_min_posts(test_session: AsyncSession):
    """Topics below min_posts threshold are excluded."""
    # Insert only 2 posts — below min_posts=3
    for i in range(2):
        _insert_post_with_sentiment(test_session, topics=["rare-topic"])
    await test_session.commit()

    with patch("app.dashboard.patch_service.PatchService") as MockPS:
        mock_ps = MagicMock()
        mock_ps.get_current_patch = AsyncMock(return_value="16.2")
        MockPS.return_value = mock_ps

        svc = AggregationService(test_session)
        aggs = await svc.aggregate_topics(period_days=7, min_posts=3)

    assert len(aggs) == 0


@pytest.mark.asyncio
async def test_aggregate_topics_empty_db(test_session: AsyncSession):
    """aggregate_topics returns empty list on empty database."""
    with patch("app.dashboard.patch_service.PatchService") as MockPS:
        mock_ps = MagicMock()
        mock_ps.get_current_patch = AsyncMock(return_value="16.2")
        MockPS.return_value = mock_ps

        svc = AggregationService(test_session)
        aggs = await svc.aggregate_topics()

    assert aggs == []


# ---------------------------------------------------------------------------
# Velocity calculation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_topic_velocity_no_aggregation(test_session: AsyncSession):
    """Velocity returns None label when topic doesn't exist."""
    svc = AggregationService(test_session)
    vel = await svc.get_topic_velocity("nonexistent-topic")
    assert vel["velocity_label"] is None
    assert vel["velocity_pct"] == 0.0


@pytest.mark.asyncio
async def test_topic_velocity_rising(test_session: AsyncSession):
    """Velocity returns 'rising' when current count > 0 and previous = 0."""
    now = datetime.now(timezone.utc)
    agg = Aggregation(
        topic_name="Test",
        topic_slug="test",
        sentiment_positive=60.0,
        sentiment_neutral=20.0,
        sentiment_negative=20.0,
        post_count=10,
        period_start=now - timedelta(days=7),
        period_end=now,
    )
    test_session.add(agg)
    await test_session.commit()

    svc = AggregationService(test_session)
    vel = await svc.get_topic_velocity("test")
    assert vel["velocity_label"] == "rising"
    assert vel["velocity_pct"] == 100.0


# ---------------------------------------------------------------------------
# get_all_topics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_all_topics_returns_list(test_session: AsyncSession):
    """get_all_topics returns topic list ordered by post_count."""
    now = datetime.now(timezone.utc)
    for name, count in [("Big Topic", 50), ("Small Topic", 5)]:
        agg = Aggregation(
            topic_name=name,
            topic_slug=slugify(name),
            sentiment_positive=60.0,
            sentiment_neutral=20.0,
            sentiment_negative=20.0,
            post_count=count,
            period_start=now - timedelta(days=7),
            period_end=now,
        )
        test_session.add(agg)
    await test_session.commit()

    svc = AggregationService(test_session)
    topics = await svc.get_all_topics()

    assert len(topics) == 2
    assert topics[0]["name"] == "Big Topic"
    assert topics[0]["post_count"] == 50
    assert topics[1]["name"] == "Small Topic"


# ---------------------------------------------------------------------------
# calculate_pulse_score
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pulse_score_empty_db(test_session: AsyncSession):
    """Pulse score returns 0 / Critical on empty DB."""
    svc = AggregationService(test_session)
    result = await svc.calculate_pulse_score()
    assert result["pulse_score"] == 0
    assert result["label"] == "Critical"


@pytest.mark.asyncio
async def test_pulse_score_with_data(test_session: AsyncSession):
    """Pulse score computes weighted score from aggregations."""
    now = datetime.now(timezone.utc)
    # Create 5 aggregations to max out topic_diversity
    for i in range(5):
        agg = Aggregation(
            topic_name=f"Topic {i}",
            topic_slug=f"topic-{i}",
            sentiment_positive=70.0,
            sentiment_neutral=20.0,
            sentiment_negative=10.0,
            post_count=15,
            period_start=now - timedelta(days=7),
            period_end=now,
        )
        test_session.add(agg)
    await test_session.commit()

    svc = AggregationService(test_session)
    result = await svc.calculate_pulse_score()

    assert result["pulse_score"] > 0
    assert result["label"] in ("Critical", "Mixed", "Healthy")
    assert "breakdown" in result


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stats_empty_db(test_session: AsyncSession):
    """Stats returns zeroed values on empty DB."""
    svc = AggregationService(test_session)
    stats = await svc.get_stats()

    assert stats["posts_analyzed"] == 0
    assert stats["active_topics"] == 0
    assert stats["sources_active"] == 0


# ---------------------------------------------------------------------------
# get_source_distribution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_source_distribution(test_session: AsyncSession):
    """Source distribution counts posts per platform."""
    now = datetime.now(timezone.utc)
    for platform in [Platform.REDDIT, Platform.REDDIT, Platform.YOUTUBE]:
        post = Post(
            id=str(uuid4()),
            platform=platform,
            external_id=str(uuid4()),
            title="Test",
            content="Content",
            author="tester",
            url="https://example.com",
            created_at=now,
            fetched_at=now,
            updated_at=now,
        )
        test_session.add(post)
    await test_session.commit()

    svc = AggregationService(test_session)
    dist = await svc.get_source_distribution()

    assert dist["reddit"] == 2
    assert dist["youtube"] == 1


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


def test_slugify_basic():
    assert slugify("Balance Changes") == "balance-changes"


def test_slugify_special_chars():
    assert slugify("What's New?!") == "whats-new"
