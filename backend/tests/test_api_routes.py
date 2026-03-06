"""Tests for key API endpoints — dashboard, health, topics, feedback."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Aggregation, Post, Platform, SentimentResult, SentimentLabel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_aggregation(
    session: AsyncSession,
    name: str = "Test Topic",
    slug: str = "test-topic",
    post_count: int = 10,
) -> Aggregation:
    now = datetime.now(timezone.utc)
    agg = Aggregation(
        topic_name=name,
        topic_slug=slug,
        sentiment_positive=60.0,
        sentiment_neutral=25.0,
        sentiment_negative=15.0,
        post_count=post_count,
        source_mix={"reddit": post_count},
        representative_quotes=[],
        period_start=now - timedelta(days=7),
        period_end=now,
        confidence_score=0.8,
    )
    session.add(agg)
    return agg


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_returns_status(client: AsyncClient):
    """Health endpoint returns a valid health status."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "unhealthy", "degraded")
    assert "database" in data
    assert "version" in data


# ---------------------------------------------------------------------------
# GET /api/dashboard/topics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_topics_list_empty(client: AsyncClient):
    """Topics endpoint returns empty list on empty DB."""
    response = await client.get("/api/dashboard/topics")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert isinstance(data["topics"], list)
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_topics_list_with_data(client: AsyncClient, test_session: AsyncSession):
    """Topics endpoint returns topics when data exists."""
    _make_aggregation(test_session, "Balance", "balance", 20)
    _make_aggregation(test_session, "Ranked", "ranked", 10)
    await test_session.commit()

    response = await client.get("/api/dashboard/topics")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["topics"][0]["name"] == "Balance"  # ordered by post_count desc


# ---------------------------------------------------------------------------
# GET /api/dashboard/topics/{slug}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_topic_by_slug_found(client: AsyncClient, test_session: AsyncSession):
    """Topic detail endpoint returns topic data."""
    _make_aggregation(test_session, "Balance", "balance")
    await test_session.commit()

    response = await client.get("/api/dashboard/topics/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "balance"
    assert "sentiment" in data


@pytest.mark.asyncio
async def test_topic_by_slug_not_found(client: AsyncClient):
    """Topic detail returns 404 for nonexistent slug."""
    response = await client.get("/api/dashboard/topics/nonexistent")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/dashboard/trending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trending_returns_structure(client: AsyncClient):
    """Trending endpoint returns expected structure."""
    response = await client.get("/api/dashboard/trending")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert "count" in data
    assert "filters" in data


# ---------------------------------------------------------------------------
# GET /api/dashboard/pulse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pulse_returns_score(client: AsyncClient):
    """Pulse endpoint returns pulse score structure."""
    response = await client.get("/api/dashboard/pulse")
    assert response.status_code == 200
    data = response.json()
    assert "pulse_score" in data
    assert "label" in data
    assert "breakdown" in data


# ---------------------------------------------------------------------------
# GET /api/dashboard/stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stats_returns_structure(client: AsyncClient):
    """Stats endpoint returns expected keys."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "posts_analyzed" in data
    assert "active_topics" in data
    assert "sources_active" in data
    assert "pulse_score" in data


# ---------------------------------------------------------------------------
# GET /api/dashboard/sources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sources_empty(client: AsyncClient):
    """Sources endpoint returns empty on no data."""
    response = await client.get("/api/dashboard/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "total" in data
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# POST /api/feedback/vote — valid input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_feedback_vote_valid(client: AsyncClient):
    """Feedback vote accepts valid input."""
    response = await client.post(
        "/api/feedback/vote",
        json={
            "topic_slug": "test-topic",
            "vote_type": "thumbs_up",
            "session_id": "test-session-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_feedback_vote_invalid(client: AsyncClient):
    """Feedback vote rejects invalid vote type."""
    response = await client.post(
        "/api/feedback/vote",
        json={
            "topic_slug": "test-topic",
            "vote_type": "invalid_type",
            "session_id": "test-session-002",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/feedback/report
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_feedback_report_valid(client: AsyncClient):
    """Feedback report accepts valid input."""
    response = await client.post(
        "/api/feedback/report",
        json={
            "topic_slug": "test-topic",
            "reason": "misleading",
            "details": "The sentiment seems wrong",
            "session_id": "test-session-003",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# ---------------------------------------------------------------------------
# POST /api/feedback/general
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_feedback_general_valid(client: AsyncClient):
    """General feedback accepts valid input."""
    response = await client.post(
        "/api/feedback/general",
        json={
            "message": "Great dashboard!",
            "session_id": "test-session-004",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
