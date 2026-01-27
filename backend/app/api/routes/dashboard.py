"""Dashboard API routes for trending topics and sentiment data."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.dashboard.service import AggregationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard")


@router.get("/trending")
async def get_trending(
    db: Annotated[AsyncSession, Depends(get_db)],
    theme: Annotated[list[str] | None, Query(description="Filter by themes")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict:
    """Get trending topics with sentiment data.

    Args:
        db: Database session.
        theme: Optional list of theme names to filter by.
        limit: Maximum topics to return (1-50).

    Returns:
        Dict containing list of trending topics.
    """
    service = AggregationService(db)
    topics = await service.get_trending(themes=theme, limit=limit)

    return {
        "topics": topics,
        "count": len(topics),
        "filters": {
            "themes": theme,
            "limit": limit,
        },
    }


@router.get("/topics")
async def list_topics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get all topics for navigation.

    Returns:
        Dict containing list of all topics with basic info.
    """
    service = AggregationService(db)
    topics = await service.get_all_topics()

    return {
        "topics": topics,
        "count": len(topics),
    }


@router.get("/topics/{slug}")
async def get_topic(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get a single topic by slug.

    Args:
        slug: URL-safe topic slug.
        db: Database session.

    Returns:
        Topic data dict.

    Raises:
        HTTPException: If topic not found.
    """
    service = AggregationService(db)
    topic = await service.get_topic_by_slug(slug)

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic


@router.get("/sources")
async def get_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get overall source distribution.

    Returns:
        Dict mapping platform names to post counts.
    """
    service = AggregationService(db)
    distribution = await service.get_source_distribution()

    total = sum(distribution.values())
    percentages = {
        platform: round(count / total * 100, 1) if total else 0
        for platform, count in distribution.items()
    }

    return {
        "sources": distribution,
        "percentages": percentages,
        "total": total,
    }


@router.post("/aggregate")
async def trigger_aggregation(
    db: Annotated[AsyncSession, Depends(get_db)],
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    min_posts: Annotated[int, Query(ge=1, le=100)] = 3,
) -> dict:
    """Manually trigger topic aggregation.

    Args:
        db: Database session.
        period_days: Number of days to aggregate (1-30).
        min_posts: Minimum posts for topic inclusion (1-100).

    Returns:
        Dict with aggregation results.
    """
    service = AggregationService(db)

    try:
        aggregations = await service.aggregate_topics(
            period_days=period_days,
            min_posts=min_posts,
        )
        return {
            "status": "success",
            "topics_aggregated": len(aggregations),
            "config": {
                "period_days": period_days,
                "min_posts": min_posts,
            },
        }
    except Exception as e:
        logger.exception("Aggregation failed")
        raise HTTPException(status_code=500, detail=str(e))
