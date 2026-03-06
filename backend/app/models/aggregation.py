"""Aggregation model for topic summaries with sentiment breakdowns."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

# Dialect-aware JSON type: JSONB on PostgreSQL, plain JSON on SQLite (tests)
JSONVariant = JSON().with_variant(JSONB(), "postgresql")

from app.database import Base


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Aggregation(Base):
    """Aggregated topic summaries with sentiment breakdowns."""

    __tablename__ = "aggregations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Topic identification
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Aggregated sentiment
    sentiment_positive: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Percentage 0-100
    sentiment_neutral: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_negative: Mapped[float] = mapped_column(Float, default=0.0)

    # Summary
    summary: Mapped[str | None] = mapped_column(Text)
    representative_quotes: Mapped[list | None] = mapped_column(
        JSONVariant
    )  # [{"text": "...", "source_url": "..."}]

    # Stats
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    source_mix: Mapped[dict | None] = mapped_column(
        JSONVariant
    )  # {"reddit": 45, "youtube": 30, ...}

    # Time window
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Patch context (optional)
    patch_version: Mapped[str | None] = mapped_column(String(20))  # e.g., "14.10"

    # Confidence/transparency
    confidence_score: Mapped[float | None] = mapped_column(Float)
    sentiment_explanation: Mapped[dict | None] = mapped_column(JSONVariant)
    confidence_breakdown: Mapped[dict | None] = mapped_column(JSONVariant)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = ({"comment": "Aggregated topic summaries with sentiment breakdowns"},)
