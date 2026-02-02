"""Digest service for generating AI-powered topic summaries.

This service creates personalized digests from followed topics,
using Gemini API for natural language summaries.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def generate_digest_summary(
    topics: list[dict],
) -> dict:
    """Generate an AI-powered summary of followed topics.

    Args:
        topics: List of topic dicts with name, summary, sentiment, post_count.

    Returns:
        Dict with summary text and metadata.
    """
    settings = get_settings()

    if not topics:
        return {
            "summary": "No topics to summarize. Follow some topics to get a personalized digest!",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "topic_count": 0,
            "is_ai_generated": False,
        }

    # Build context from topics
    topic_context = _build_topic_context(topics)

    # If Gemini is configured, use AI summary
    if settings.gemini_api_key:
        try:
            summary = await _generate_gemini_summary(topic_context, settings)
            return {
                "summary": summary,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "topic_count": len(topics),
                "is_ai_generated": True,
            }
        except Exception as e:
            logger.warning("Gemini summary failed, using fallback: %s", e)

    # Fallback: generate a simple structured summary
    summary = _generate_fallback_summary(topics)
    return {
        "summary": summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic_count": len(topics),
        "is_ai_generated": False,
    }


def _build_topic_context(topics: list[dict]) -> str:
    """Build context string from topics for the AI prompt."""
    lines = []
    for topic in topics:
        name = topic.get("name", "Unknown")
        summary = topic.get("summary", "No summary available")
        sentiment = topic.get("sentiment", {})
        post_count = topic.get("post_count", 0)

        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        sentiment_str = "positive" if pos > neg else "negative" if neg > pos else "mixed"

        lines.append(f"- {name}: {summary} (Sentiment: {sentiment_str}, {post_count} posts)")

    return "\n".join(lines)


async def _generate_gemini_summary(context: str, settings) -> str:
    """Generate summary using Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"

    prompt = f"""You are a gaming community analyst. Create a brief, engaging daily digest summary based on these community topics:

{context}

Requirements:
- 2-3 paragraphs maximum
- Highlight the most important or trending discussions
- Mention overall community sentiment
- Keep it conversational and informative
- Don't use bullet points, write in prose
- Don't include greetings or sign-offs

Write the digest summary:"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
            "topP": 0.9,
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()


def _generate_fallback_summary(topics: list[dict]) -> str:
    """Generate a simple fallback summary without AI."""
    if not topics:
        return "No topics to summarize."

    # Sort by post count to find most active
    sorted_topics = sorted(topics, key=lambda t: t.get("post_count", 0), reverse=True)

    # Calculate overall sentiment
    total_pos = sum(t.get("sentiment", {}).get("positive", 0) for t in topics)
    total_neg = sum(t.get("sentiment", {}).get("negative", 0) for t in topics)
    total_neutral = sum(t.get("sentiment", {}).get("neutral", 0) for t in topics)

    if total_pos > total_neg and total_pos > total_neutral:
        overall_mood = "generally positive"
    elif total_neg > total_pos and total_neg > total_neutral:
        overall_mood = "showing some concerns"
    else:
        overall_mood = "mixed"

    # Build summary
    parts = []

    # Opening
    parts.append(f"Your digest covers {len(topics)} topic{'s' if len(topics) > 1 else ''} you're following.")

    # Most active topic
    if sorted_topics:
        top = sorted_topics[0]
        parts.append(
            f"The most active discussion is around {top.get('name', 'Unknown')} "
            f"with {top.get('post_count', 0)} posts."
        )

    # Sentiment
    parts.append(f"Community sentiment is {overall_mood} across your followed topics.")

    # Quick summaries of top 3
    if len(sorted_topics) > 1:
        summaries = []
        for topic in sorted_topics[:3]:
            summary = topic.get("summary", "")
            if summary and len(summary) > 50:
                summary = summary[:50] + "..."
            if summary:
                summaries.append(f"{topic.get('name', 'Unknown')}: {summary}")

        if summaries:
            parts.append("Key highlights: " + " | ".join(summaries))

    return " ".join(parts)
