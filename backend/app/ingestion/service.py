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


def _platform_from_string(platform: str) -> Platform:
    """Convert platform string to Platform enum."""
    return Platform(platform.lower())


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
