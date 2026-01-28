"""Feedback model for user votes and reports."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class FeedbackType(str, Enum):
    """Type of feedback: vote or report."""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REPORT = "report"


class Feedback(Base):
    """User feedback on topic summaries."""

    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Topic identification
    topic_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Feedback type
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Report reason (only for report type)
    reason: Mapped[str | None] = mapped_column(String(100))

    # Optional details
    details: Mapped[str | None] = mapped_column(Text)

    # Anonymous session identifier (for rate limiting)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    __table_args__ = ({"comment": "User feedback on topic summaries"},)
