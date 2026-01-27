"""Ingestion service for orchestrating data source fetching and storage."""

import logging
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.adapters.base import DataSourceAdapter, IngestedPost
from app.models.post import Platform, Post

logger = logging.getLogger(__name__)


def _platform_from_string(platform: str) -> str:
    """Validate and normalize platform string."""
    normalized = platform.lower()
    # Validate it's a known platform
    Platform(normalized)
    return normalized


async def upsert_posts(
    session: AsyncSession,
    posts: Sequence[IngestedPost],
) -> dict[str, int]:
    """
    Upsert posts to database, returning counts.

    Uses PostgreSQL ON CONFLICT to:
    - Insert new posts
    - Update engagement metrics on existing posts (upvotes, comments_count)
    - Update fetched_at and updated_at timestamps

    Returns:
        dict with keys: fetched, upserted
    """
    if not posts:
        return {"fetched": 0, "upserted": 0}

    values = [
        {
            "platform": _platform_from_string(p.platform),
            "external_id": p.external_id,
            "title": p.title,
            "content": p.content,
            "author": p.author,
            "url": p.url,
            "upvotes": p.upvotes,
            "comments_count": p.comments_count,
            "published_at": p.published_at,
            "fetched_at": datetime.now(timezone.utc),
        }
        for p in posts
    ]

    stmt = insert(Post).values(values)

    # ON CONFLICT: update engagement metrics and timestamps
    stmt = stmt.on_conflict_do_update(
        index_elements=["platform", "external_id"],
        set_={
            "upvotes": stmt.excluded.upvotes,
            "comments_count": stmt.excluded.comments_count,
            "fetched_at": stmt.excluded.fetched_at,
            "updated_at": func.now(),
        },
    )

    result = await session.execute(stmt)
    await session.commit()

    logger.info(
        "Upserted %d posts (fetched %d)",
        result.rowcount,
        len(posts),
    )

    return {
        "fetched": len(posts),
        "upserted": result.rowcount,
    }


class IngestionService:
    """Orchestrates data ingestion from multiple sources."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self._session = session
        self._adapters: dict[str, DataSourceAdapter] = {}

    def register_adapter(self, adapter: DataSourceAdapter) -> None:
        """Register a data source adapter."""
        self._adapters[adapter.platform_name] = adapter
        logger.info("Registered adapter: %s", adapter.platform_name)

    async def ingest_from(
        self,
        platform: str,
        limit: int = 100,
    ) -> dict[str, int | str]:
        """
        Ingest posts from a specific platform.

        Returns:
            dict with keys: platform, fetched, upserted
        """
        adapter = self._adapters.get(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")

        # Collect posts from async generator
        posts: list[IngestedPost] = []
        async for post in adapter.fetch_posts(limit=limit):
            posts.append(post)

        result = await upsert_posts(self._session, posts)

        return {
            "platform": platform,
            **result,
        }

    async def ingest_all(self, limit: int = 100) -> list[dict]:
        """
        Ingest from all registered platforms.

        Returns:
            List of results per platform
        """
        results = []
        for platform in self._adapters:
            try:
                result = await self.ingest_from(platform, limit)
                results.append(result)
            except Exception as e:
                logger.error("Failed to ingest from %s: %s", platform, e)
                results.append({
                    "platform": platform,
                    "error": str(e),
                })
        return results

    async def close_all(self) -> None:
        """Close all adapter connections."""
        for name, adapter in self._adapters.items():
            try:
                await adapter.close()
                logger.info("Closed adapter: %s", name)
            except Exception as e:
                logger.error("Error closing adapter %s: %s", name, e)
