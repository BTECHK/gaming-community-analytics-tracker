"""Tests for feedback API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_vote_thumbs_up(client: AsyncClient):
    """Test submitting a thumbs up vote."""
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
    assert "Vote submitted" in data["message"]


@pytest.mark.asyncio
async def test_submit_vote_thumbs_down(client: AsyncClient):
    """Test submitting a thumbs down vote."""
    response = await client.post(
        "/api/feedback/vote",
        json={
            "topic_slug": "another-topic",
            "vote_type": "thumbs_down",
            "session_id": "test-session-002",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_submit_vote_invalid_type(client: AsyncClient):
    """Test submitting a vote with invalid type returns 422."""
    response = await client.post(
        "/api/feedback/vote",
        json={
            "topic_slug": "test-topic",
            "vote_type": "invalid",
            "session_id": "test-session-003",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_report(client: AsyncClient):
    """Test submitting a report."""
    response = await client.post(
        "/api/feedback/report",
        json={
            "topic_slug": "test-topic",
            "reason": "misleading",
            "details": "The summary doesn't match the actual sentiment.",
            "session_id": "test-session-004",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Report submitted" in data["message"]


@pytest.mark.asyncio
async def test_submit_report_all_reasons(client: AsyncClient):
    """Test all valid report reasons."""
    reasons = ["misleading", "inaccurate_quotes", "wrong_sentiment", "other"]

    for reason in reasons:
        response = await client.post(
            "/api/feedback/report",
            json={
                "topic_slug": f"topic-{reason}",
                "reason": reason,
                "session_id": f"test-session-{reason}",
            },
        )
        assert response.status_code == 200, f"Failed for reason: {reason}"


@pytest.mark.asyncio
async def test_submit_report_invalid_reason(client: AsyncClient):
    """Test submitting a report with invalid reason returns 422."""
    response = await client.post(
        "/api/feedback/report",
        json={
            "topic_slug": "test-topic",
            "reason": "invalid_reason",
            "session_id": "test-session-005",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_general_feedback(client: AsyncClient):
    """Test submitting general feedback."""
    response = await client.post(
        "/api/feedback/general",
        json={
            "message": "Great dashboard! Love the sentiment analysis.",
            "email": "user@example.com",
            "session_id": "test-session-006",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Thank you" in data["message"]


@pytest.mark.asyncio
async def test_submit_general_feedback_no_email(client: AsyncClient):
    """Test submitting general feedback without email."""
    response = await client.post(
        "/api/feedback/general",
        json={
            "message": "Feedback without email",
            "session_id": "test-session-007",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_submit_feedback_missing_session_id(client: AsyncClient):
    """Test that missing session_id returns 422."""
    response = await client.post(
        "/api/feedback/vote",
        json={
            "topic_slug": "test-topic",
            "vote_type": "thumbs_up",
            # Missing session_id
        },
    )
    assert response.status_code == 422
