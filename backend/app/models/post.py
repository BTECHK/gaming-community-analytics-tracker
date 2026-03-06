"""Post model for storing ingested content from various platforms."""

import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Platform(str, enum.Enum):
    """Supported content platforms."""

    YOUTUBE = "youtube"
    RIOT = "official-news"
    TierSite = "tier-site"
    GOOGLE_TRENDS = "google_trends"
    GUIDE_SITE = "guide-site"
    NEWS_SOURCE_A = "news-source-a"
    NEWS_SOURCE_B = "news-source-b"
    REDDIT = "reddit"


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Post(Base):
    """Raw ingested posts from various platforms."""

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    platform: Mapped[str] = mapped_column(
        SQLEnum(
            Platform,
            name="platform_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # Platform-specific ID

    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Engagement metrics
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        # Unique constraint on platform + external_id for deduplication
        Index(
            "ix_posts_platform_external_id",
            "platform",
            "external_id",
            unique=True,
        ),
        {"comment": "Raw ingested posts from various platforms"},
    )
