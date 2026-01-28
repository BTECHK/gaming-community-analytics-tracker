"""Feedback API routes for votes and reports."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.feedback import Feedback, FeedbackType
from app.schemas.feedback import (
    FeedbackResponse,
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
