"""Topic naming service using Gemini API for human-readable topic names.

This service takes BERTopic's extracted keywords and generates
concise, human-readable topic names using Google's Gemini API.
"""

import asyncio
import logging
from functools import lru_cache

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Cache for topic names to avoid repeated API calls
_topic_name_cache: dict[str, str] = {}

# Fallback names when API is unavailable
FALLBACK_TOPIC_NAMES = {
    "matchmaking": "Ranked & Matchmaking",
    "toxic": "Player Behavior",
    "balance": "Game Balance",
    "client": "Client Issues",
    "champion": "Champions & Abilities",
    "meta": "Meta Discussion",
    "patch": "Patch Notes",
    "skin": "Skins & Cosmetics",
    "esports": "Esports & Pro Play",
    "bug": "Bugs & Glitches",
    "ranked": "Ranked Play",
    "nerf": "Nerfs & Buffs",
    "rework": "Champion Reworks",
    "new": "New Content",
    "server": "Server Issues",
}


def _get_fallback_name(keywords: list[str]) -> str:
    """Get a fallback name based on keyword matching."""
    keywords_lower = [k.lower() for k in keywords]

    for key, name in FALLBACK_TOPIC_NAMES.items():
        if key in keywords_lower:
            return name

    # If no match, use the first keyword capitalized
    if keywords:
        return keywords[0].title()
    return "General Discussion"


async def generate_topic_name(
    keywords: list[str],
    context_examples: list[str] | None = None,
) -> str:
    """Generate a human-readable topic name from keywords using Gemini.

    Args:
        keywords: List of keywords extracted by BERTopic (usually top 10).
        context_examples: Optional list of example post snippets for context.

    Returns:
        A concise, human-readable topic name (2-4 words).
    """
    settings = get_settings()

    # Check cache first
    cache_key = ",".join(sorted(keywords[:5]))  # Use top 5 for cache key
    if cache_key in _topic_name_cache:
        return _topic_name_cache[cache_key]

    # If Gemini API key not configured, use fallback
    if not settings.gemini_api_key:
        logger.debug("Gemini API key not configured, using fallback naming")
        name = _get_fallback_name(keywords)
        _topic_name_cache[cache_key] = name
        return name

    if not settings.topic_naming_enabled:
        logger.debug("Topic naming disabled, using fallback")
        name = _get_fallback_name(keywords)
        _topic_name_cache[cache_key] = name
        return name

    # Build prompt for Gemini
    prompt = _build_naming_prompt(keywords, context_examples)

    try:
        name = await _call_gemini_api(prompt, settings)
        # Clean and validate the response
        name = _clean_topic_name(name)
        _topic_name_cache[cache_key] = name
        logger.info("Generated topic name: '%s' from keywords: %s", name, keywords[:5])
        return name
    except Exception as e:
        logger.warning("Gemini API call failed: %s, using fallback", e)
        name = _get_fallback_name(keywords)
        _topic_name_cache[cache_key] = name
        return name


def _build_naming_prompt(
    keywords: list[str],
    context_examples: list[str] | None = None,
) -> str:
    """Build the prompt for topic naming."""
    prompt_parts = [
        "You are naming topics for a gaming community dashboard.",
        "Given these keywords extracted from community posts, generate a concise topic name.",
        "",
        "Requirements:",
        "- 2-4 words maximum",
        "- Clear and descriptive",
        "- Suitable for a dashboard category",
        "- No quotes or punctuation",
        "",
        f"Keywords: {', '.join(keywords[:10])}",
    ]

    if context_examples:
        prompt_parts.extend([
            "",
            "Example post snippets from this topic:",
        ])
        for i, example in enumerate(context_examples[:3], 1):
            # Truncate long examples
            example_text = example[:200] + "..." if len(example) > 200 else example
            prompt_parts.append(f"{i}. {example_text}")

    prompt_parts.extend([
        "",
        "Respond with ONLY the topic name, nothing else.",
    ])

    return "\n".join(prompt_parts)


async def _call_gemini_api(prompt: str, settings) -> str:
    """Call the Gemini API to generate a topic name."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"

    headers = {
        "Content-Type": "application/json",
    }

    params = {
        "key": settings.gemini_api_key,
    }

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,  # Low temperature for consistent naming
            "maxOutputTokens": 20,  # Short response
            "topP": 0.8,
        },
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()

        # Extract text from Gemini response
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected Gemini response format: {e}")


def _clean_topic_name(name: str) -> str:
    """Clean and validate the generated topic name."""
    # Remove quotes, extra whitespace
    name = name.strip().strip('"\'')

    # Limit length
    words = name.split()
    if len(words) > 4:
        words = words[:4]
    name = " ".join(words)

    # Title case
    name = name.title()

    # Remove trailing punctuation
    name = name.rstrip(".,!?;:")

    return name


async def batch_generate_topic_names(
    topics_keywords: list[list[str]],
) -> list[str]:
    """Generate names for multiple topics efficiently.

    Args:
        topics_keywords: List of keyword lists, one per topic.

    Returns:
        List of topic names in the same order.
    """
    # Run all naming requests concurrently
    tasks = [generate_topic_name(keywords) for keywords in topics_keywords]
    return await asyncio.gather(*tasks)


def clear_topic_name_cache() -> None:
    """Clear the topic name cache."""
    global _topic_name_cache
    _topic_name_cache = {}
    logger.info("Topic name cache cleared")
