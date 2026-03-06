"""Dashboard API routes for trending topics and sentiment data."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.dashboard.service import AggregationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard")


@router.get("/patch-pulse")
async def get_patch_pulse(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> dict:
    """Get Patch Pulse data for current patch.

    Returns patch-specific sentiment data including topics, overall sentiment,
    and total posts analyzed.

    Args:
        db: Database session.
        limit: Maximum topics to return (1-20).

    Returns:
        Dict with patch info, topics, and overall sentiment.
    """
    from app.dashboard.patch_service import PatchService

    patch_service = PatchService()
    current_patch = await patch_service.get_current_patch()

    service = AggregationService(db)
    pulse_data = await service.get_patch_pulse(current_patch, limit=limit)

    response = {
        "patch": current_patch,
        "topics": pulse_data["topics"],
        "overall_sentiment": pulse_data["overall_sentiment"],
        "total_posts": pulse_data["total_posts"],
        "last_updated": datetime.utcnow().isoformat(),
    }

    # Include message if present (e.g., "no patch data yet")
    if "message" in pulse_data:
        response["message"] = pulse_data["message"]

    return response


@router.get("/trending")
async def get_trending(
    db: Annotated[AsyncSession, Depends(get_db)],
    theme: Annotated[list[str] | None, Query(description="Filter by themes")] = None,
    platform: Annotated[list[str] | None, Query(description="Filter by platforms (youtube, official-news, tier-site, guide-site)")] = None,
    period_days: Annotated[int, Query(ge=1, le=30, description="Filter by time period in days")] = 7,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict:
    """Get trending topics with sentiment data.

    Args:
        db: Database session.
        theme: Optional list of theme names to filter by.
        platform: Optional list of platform names to filter by.
        period_days: Number of days to look back (1-30, default 7).
        limit: Maximum topics to return (1-50).

    Returns:
        Dict containing list of trending topics.
    """
    service = AggregationService(db)
    topics, last_updated = await service.get_trending(
        themes=theme, platforms=platform, period_days=period_days, limit=limit,
    )

    return {
        "topics": topics,
        "count": len(topics),
        "last_updated": last_updated,
        "filters": {
            "themes": theme,
            "platforms": platform,
            "period_days": period_days,
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


@router.post("/digest/summary")
async def generate_digest_summary(
    slugs: list[str],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Generate an AI-powered summary of followed topics.

    Args:
        slugs: List of topic slugs to include in the digest.
        db: Database session.

    Returns:
        Dict with summary text and metadata.
    """
    from app.services.digest import generate_digest_summary as gen_summary

    service = AggregationService(db)

    # Fetch topic data for each slug
    topics = []
    for slug in slugs[:10]:  # Limit to 10 topics
        topic = await service.get_topic_by_slug(slug)
        if topic:
            topics.append(topic)

    # Generate summary
    result = await gen_summary(topics)
    return result
