"""Feedback API routes for votes and reports."""

import logging
import time
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.feedback import Feedback, FeedbackType
from app.schemas.feedback import (
    FeedbackResponse,
    GeneralFeedbackRequest,
    ReportRequest,
    VoteRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback")

# ---------------------------------------------------------------------------
# In-memory sliding-window rate limiter
# ---------------------------------------------------------------------------

# Config
RATE_LIMIT_MAX_REQUESTS = 5  # max submissions per window
RATE_LIMIT_WINDOW_SECONDS = 60  # 1-minute sliding window

# Storage: IP → list of timestamps
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str) -> tuple[bool, int]:
    """Check if a client IP is within the rate limit.

    Returns:
        Tuple of (allowed: bool, retry_after_seconds: int).
    """
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    # Prune timestamps outside the window
    timestamps = _rate_limit_store[client_ip]
    _rate_limit_store[client_ip] = [t for t in timestamps if t > window_start]
    timestamps = _rate_limit_store[client_ip]

    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        # Calculate when the oldest timestamp in the window will expire
        oldest = timestamps[0]
        retry_after = int(oldest - window_start) + 1
        return False, max(retry_after, 1)

    # Record this request
    _rate_limit_store[client_ip].append(now)
    return True, 0


def _enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency that raises 429 if rate limit exceeded."""
    client_ip = _get_client_ip(request)
    allowed, retry_after = _check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many feedback submissions. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/vote", response_model=FeedbackResponse)
async def submit_vote(
    request: VoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    http_request: Request = None,
    _rate_limit: None = Depends(_enforce_rate_limit),
) -> FeedbackResponse:
    """Submit a thumbs up or down vote on a topic summary.

    Args:
        request: Vote request with topic slug, vote type, and session ID.
        db: Database session.

    Returns:
        Success response.
    """
    feedback = Feedback(
        topic_slug=request.topic_slug,
        feedback_type=request.vote_type.value,
        session_id=request.session_id,
    )

    db.add(feedback)
    await db.commit()

    logger.info(
        f"Vote submitted: {request.vote_type.value} for {request.topic_slug}"
    )

    return FeedbackResponse(
        success=True,
        message="Vote submitted successfully",
    )


@router.post("/report", response_model=FeedbackResponse)
async def submit_report(
    request: ReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(_enforce_rate_limit),
) -> FeedbackResponse:
    """Submit a report for a misleading or inaccurate summary.

    Args:
        request: Report request with topic slug, reason, optional details.
        db: Database session.

    Returns:
        Success response.
    """
    feedback = Feedback(
        topic_slug=request.topic_slug,
        feedback_type=FeedbackType.REPORT.value,
        reason=request.reason.value,
        details=request.details,
        session_id=request.session_id,
    )

    db.add(feedback)
    await db.commit()

    logger.info(
        f"Report submitted: {request.reason.value} for {request.topic_slug}"
    )

    return FeedbackResponse(
        success=True,
        message="Report submitted successfully. Thank you for your feedback.",
    )


@router.post("/general", response_model=FeedbackResponse)
async def submit_general_feedback(
    request: GeneralFeedbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(_enforce_rate_limit),
) -> FeedbackResponse:
    """Submit general feedback about the application.

    Args:
        request: General feedback with message, optional email, and session ID.
        db: Database session.

    Returns:
        Success response.
    """
    feedback = Feedback(
        topic_slug="__general__",  # Special slug for general feedback
        feedback_type=FeedbackType.GENERAL.value,
        details=request.message,
        reason=request.email,  # Reuse reason field for email (optional)
        session_id=request.session_id,
    )

    db.add(feedback)
    await db.commit()

    logger.info(f"General feedback submitted from session {request.session_id[:8]}...")

    return FeedbackResponse(
        success=True,
        message="Thank you for your feedback!",
    )
