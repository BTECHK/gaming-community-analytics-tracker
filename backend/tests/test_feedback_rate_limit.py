"""Tests for feedback rate limiting — allows, blocks, and IP independence."""

import pytest
from httpx import AsyncClient

from app.api.routes.feedback import RATE_LIMIT_MAX_REQUESTS


def _vote_payload(session_id: str = "test-session") -> dict:
    return {
        "topic_slug": "test-topic",
        "vote_type": "thumbs_up",
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Allows requests under the limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_allows_requests_under_limit(client: AsyncClient):
    """Requests up to the limit should succeed (200)."""
    for i in range(RATE_LIMIT_MAX_REQUESTS):
        response = await client.post(
            "/api/feedback/vote",
            json=_vote_payload(f"session-{i}"),
        )
        assert response.status_code == 200, f"Request {i + 1} should succeed"


# ---------------------------------------------------------------------------
# Returns 429 when limit exceeded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_429_when_exceeded(client: AsyncClient):
    """The (RATE_LIMIT_MAX_REQUESTS + 1)th request should return 429."""
    # Exhaust the limit
    for i in range(RATE_LIMIT_MAX_REQUESTS):
        resp = await client.post(
            "/api/feedback/vote",
            json=_vote_payload(f"session-{i}"),
        )
        assert resp.status_code == 200

    # Next request should be blocked
    response = await client.post(
        "/api/feedback/vote",
        json=_vote_payload("session-overflow"),
    )
    assert response.status_code == 429
    assert "retry-after" in response.headers
    data = response.json()
    assert "too many" in data["detail"].lower()


# ---------------------------------------------------------------------------
# Rate limit applies to all feedback endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_applies_to_report(client: AsyncClient):
    """Rate limit also protects the /report endpoint."""
    # Exhaust limit via /vote
    for i in range(RATE_LIMIT_MAX_REQUESTS):
        await client.post("/api/feedback/vote", json=_vote_payload(f"s-{i}"))

    # /report should also be blocked for the same IP
    response = await client.post(
        "/api/feedback/report",
        json={
            "topic_slug": "test-topic",
            "reason": "misleading",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_applies_to_general(client: AsyncClient):
    """Rate limit also protects the /general endpoint."""
    for i in range(RATE_LIMIT_MAX_REQUESTS):
        await client.post("/api/feedback/vote", json=_vote_payload(f"s-{i}"))

    response = await client.post(
        "/api/feedback/general",
        json={
            "message": "Great app!",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 429


# ---------------------------------------------------------------------------
# Different IPs are independent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_different_ips_independent(client: AsyncClient):
    """Different IPs should have independent rate limits."""
    # Exhaust limit for IP "1.2.3.4"
    for i in range(RATE_LIMIT_MAX_REQUESTS):
        resp = await client.post(
            "/api/feedback/vote",
            json=_vote_payload(f"s-a-{i}"),
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        assert resp.status_code == 200

    # IP "1.2.3.4" should be blocked
    resp_blocked = await client.post(
        "/api/feedback/vote",
        json=_vote_payload("s-a-overflow"),
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    assert resp_blocked.status_code == 429

    # IP "5.6.7.8" should still be allowed
    resp_other = await client.post(
        "/api/feedback/vote",
        json=_vote_payload("s-b-1"),
        headers={"X-Forwarded-For": "5.6.7.8"},
    )
    assert resp_other.status_code == 200
