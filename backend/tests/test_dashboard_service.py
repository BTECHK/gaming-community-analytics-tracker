"""Tests for AggregationService dashboard methods — get_trending, filtering, empty states."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Aggregation
from app.dashboard.service import AggregationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_aggregation(
    name: str,
    slug: str,
    post_count: int = 10,
    positive: float = 60.0,
    neutral: float = 25.0,
    negative: float = 15.0,
    source_mix: dict | None = None,
    patch_version: str | None = None,
) -> Aggregation:
    now = datetime.now(timezone.utc)
    return Aggregation(
        topic_name=name,
        topic_slug=slug,
        sentiment_positive=positive,
        sentiment_neutral=neutral,
        sentiment_negative=negative,
        post_count=post_count,
        source_mix=source_mix or {"reddit": post_count},
        representative_quotes=[],
        period_start=now - timedelta(days=7),
        period_end=now,
        confidence_score=0.8,
        patch_version=patch_version,
    )


# ---------------------------------------------------------------------------
# get_trending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_trending_returns_topics(test_session: AsyncSession):
    """get_trending returns aggregated topics sorted by post_count."""
    test_session.add(_make_aggregation("Big Topic", "big-topic", post_count=50))
    test_session.add(_make_aggregation("Small Topic", "small-topic", post_count=5))
    await test_session.commit()

    svc = AggregationService(test_session)
    topics, last_updated = await svc.get_trending()

    assert len(topics) == 2
    assert topics[0]["slug"] == "big-topic"
    assert topics[0]["post_count"] == 50
    assert last_updated is not None


@pytest.mark.asyncio
async def test_get_trending_empty_db(test_session: AsyncSession):
    """get_trending returns empty list on empty DB."""
    svc = AggregationService(test_session)
    topics, last_updated = await svc.get_trending()

    assert topics == []
    assert last_updated is None


@pytest.mark.asyncio
async def test_get_trending_filters_by_platform(test_session: AsyncSession):
    """get_trending filters topics by platform when specified."""
    test_session.add(_make_aggregation(
        "Reddit Topic", "reddit-topic", source_mix={"reddit": 10},
    ))
    test_session.add(_make_aggregation(
        "YouTube Topic", "youtube-topic", source_mix={"youtube": 8},
    ))
    await test_session.commit()

    svc = AggregationService(test_session)
    topics, _ = await svc.get_trending(platforms=["reddit"])

    assert len(topics) == 1
    assert topics[0]["slug"] == "reddit-topic"


@pytest.mark.asyncio
async def test_get_trending_excludes_old_aggregations(test_session: AsyncSession):
    """get_trending excludes aggregations outside period_days window."""
    now = datetime.now(timezone.utc)
    old = _make_aggregation("Old Topic", "old-topic")
    # Set period_end to 30 days ago (outside default 7-day window)
    old.period_end = now - timedelta(days=30)
    test_session.add(old)

    test_session.add(_make_aggregation("Recent Topic", "recent-topic"))
    await test_session.commit()

    svc = AggregationService(test_session)
    topics, _ = await svc.get_trending(period_days=7)

    assert len(topics) == 1
    assert topics[0]["slug"] == "recent-topic"


# ---------------------------------------------------------------------------
# get_topic_by_slug
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_topic_by_slug_found(test_session: AsyncSession):
    """get_topic_by_slug returns topic data when found."""
    test_session.add(_make_aggregation("Balance", "balance"))
    await test_session.commit()

    svc = AggregationService(test_session)
    topic = await svc.get_topic_by_slug("balance")

    assert topic is not None
    assert topic["slug"] == "balance"
    assert topic["name"] == "Balance"
    assert "sentiment" in topic
    assert "post_count" in topic


@pytest.mark.asyncio
async def test_get_topic_by_slug_not_found(test_session: AsyncSession):
    """get_topic_by_slug returns None when topic doesn't exist."""
    svc = AggregationService(test_session)
    topic = await svc.get_topic_by_slug("nonexistent")
    assert topic is None


# ---------------------------------------------------------------------------
# get_patch_pulse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_patch_pulse_with_data(test_session: AsyncSession):
    """get_patch_pulse returns patch-specific data."""
    test_session.add(_make_aggregation(
        "Patch Topic", "patch-topic", post_count=20, patch_version="16.2",
    ))
    await test_session.commit()

    svc = AggregationService(test_session)
    result = await svc.get_patch_pulse("16.2")

    assert len(result["topics"]) == 1
    assert result["total_posts"] == 20
    assert result["overall_sentiment"]["positive"] > 0


@pytest.mark.asyncio
async def test_get_patch_pulse_empty(test_session: AsyncSession):
    """get_patch_pulse returns empty structure with message when no data."""
    svc = AggregationService(test_session)
    result = await svc.get_patch_pulse("99.99")

    assert result["topics"] == []
    assert result["total_posts"] == 0
    assert "message" in result
