"""Feedback API routes for votes and reports."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
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


@router.post("/vote", response_model=FeedbackResponse)
async def submit_vote(
    request: VoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
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
