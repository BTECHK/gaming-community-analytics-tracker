"""SentimentResult model for NLP analysis outputs."""

import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SentimentLabel(str, enum.Enum):
    """Sentiment classification labels."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class SentimentResult(Base):
    """NLP analysis results for posts."""

    __tablename__ = "sentiment_results"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    post_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("posts.id"), nullable=False, index=True
    )

    # Sentiment scores
    label: Mapped[str] = mapped_column(
        SQLEnum(SentimentLabel, name="sentiment_label_enum"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0

    # Detailed scores (optional, depends on model output)
    scores: Mapped[dict | None] = mapped_column(
        JSONB
    )  # {"positive": 0.8, "neutral": 0.15, "negative": 0.05}

    # Topic detection
    topics: Mapped[list | None] = mapped_column(
        JSONB
    )  # ["matchmaking", "balance"]

    # Toxicity flag
    is_toxic: Mapped[bool] = mapped_column(Boolean, default=False)
    toxicity_score: Mapped[float | None] = mapped_column(Float)

    # Model metadata
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50))

    # Timestamps
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # Cache TTL

    __table_args__ = ({"comment": "NLP analysis results for posts"},)
