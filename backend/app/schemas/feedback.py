"""Pydantic schemas for feedback endpoints."""

from enum import Enum

from pydantic import BaseModel, Field


class VoteType(str, Enum):
    """Vote type for thumbs up/down."""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class ReportReason(str, Enum):
    """Reasons for reporting a summary."""

    MISLEADING = "misleading"
    INACCURATE_QUOTES = "inaccurate_quotes"
    WRONG_SENTIMENT = "wrong_sentiment"
    OTHER = "other"


class VoteRequest(BaseModel):
    """Request body for voting on a summary."""

    topic_slug: str = Field(..., min_length=1, max_length=255)
    vote_type: VoteType
    session_id: str = Field(..., min_length=1, max_length=255)


class ReportRequest(BaseModel):
    """Request body for reporting a summary."""

    topic_slug: str = Field(..., min_length=1, max_length=255)
    reason: ReportReason
    details: str | None = Field(None, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=255)


class GeneralFeedbackRequest(BaseModel):
    """Request body for general feedback submission."""

    message: str = Field(..., min_length=1, max_length=2000)
    email: str | None = Field(None, max_length=255)
    session_id: str = Field(..., min_length=1, max_length=255)


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""

    success: bool
    message: str
