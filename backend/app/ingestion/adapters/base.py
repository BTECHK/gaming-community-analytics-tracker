"""Base interfaces for data source adapters."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Protocol


@dataclass
class IngestedPost:
    """Normalized post data from any platform.

    This dataclass represents a post ingested from any external platform
    (Reddit, YouTube, etc.) in a standardized format before storage.
    """

    external_id: str
    platform: str
    title: str
    content: str | None
    author: str | None
    url: str
    upvotes: int
    comments_count: int
    published_at: datetime | None
    raw_metadata: dict = field(default_factory=dict)


class DataSourceAdapter(Protocol):
    """Protocol for data source adapters.

    Implements PEP 544 structural subtyping - any class with these methods
    and properties is considered a DataSourceAdapter without explicit inheritance.
    """

    @property
    def platform_name(self) -> str:
        """Return the platform identifier (e.g., 'reddit', 'youtube')."""
        ...

    async def fetch_posts(self, limit: int = 100) -> AsyncIterator[IngestedPost]:
        """Fetch posts from the data source.

        Args:
            limit: Maximum number of posts to fetch per source.

        Yields:
            IngestedPost objects normalized from platform-specific data.
        """
        ...

    async def close(self) -> None:
        """Close any open connections and clean up resources."""
        ...
