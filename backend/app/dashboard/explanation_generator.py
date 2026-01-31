"""Explanation generator for sentiment analysis transparency.

Generates human-readable explanations for sentiment classifications
and confidence score breakdowns using algorithmic analysis of existing data.
"""

from typing import Any


def generate_sentiment_explanation(
    sentiment_positive: float,
    sentiment_neutral: float,
    sentiment_negative: float,
    source_mix: dict[str, int],
    quotes: list[dict],
    post_count: int,
) -> dict[str, Any]:
    """Generate human-readable explanation for sentiment classification.

    Analyzes sentiment distribution, source consensus, and quote patterns
    to explain why a topic is classified as positive/negative.

    Args:
        sentiment_positive: Positive sentiment percentage (0-100).
        sentiment_neutral: Neutral sentiment percentage (0-100).
        sentiment_negative: Negative sentiment percentage (0-100).
        source_mix: Dict mapping platform names to post counts.
        quotes: List of representative quote dicts.
        post_count: Total number of posts analyzed.

    Returns:
        Dict containing explanation data with factors and reasoning.
    """
    # Determine dominant sentiment
    sentiments = {
        "positive": sentiment_positive,
        "neutral": sentiment_neutral,
        "negative": sentiment_negative,
    }
    dominant_sentiment = max(sentiments, key=sentiments.get)
    dominant_value = sentiments[dominant_sentiment]

    # Calculate margin (difference from next highest)
    sorted_values = sorted(sentiments.values(), reverse=True)
    margin = sorted_values[0] - sorted_values[1] if len(sorted_values) > 1 else 100

    # Determine strength based on margin
    if margin >= 30:
        strength = "strong"
    elif margin >= 15:
        strength = "moderate"
    else:
        strength = "mixed"

    # Build factors list
    factors = []

    # Factor 1: Sentiment distribution
    if dominant_value >= 50:
        factors.append({
            "type": "sentiment_majority",
            "description": f"Majority of posts ({dominant_value:.0f}%) express {dominant_sentiment} sentiment",
            "impact": dominant_sentiment if dominant_sentiment != "neutral" else "neutral",
        })
    elif strength == "mixed":
        factors.append({
            "type": "sentiment_split",
            "description": "Community opinions are divided with no clear consensus",
            "impact": "neutral",
        })

    # Factor 2: Source consensus
    platform_count = len(source_mix)
    if platform_count >= 2:
        # Check if sentiment is consistent across sources by analyzing quotes
        platform_sentiments = _analyze_platform_sentiment(quotes)
        consensus = _check_consensus(platform_sentiments, dominant_sentiment)

        if consensus:
            factors.append({
                "type": "source_consensus",
                "description": f"Consistent sentiment across {platform_count} platforms",
                "impact": dominant_sentiment if dominant_sentiment != "neutral" else "neutral",
            })
        else:
            factors.append({
                "type": "source_divergence",
                "description": "Different platforms show varying opinions",
                "impact": "neutral",
            })

    # Factor 3: High-confidence quote distribution
    high_conf_quotes = [q for q in quotes if q.get("confidence", 0) >= 0.8]
    if high_conf_quotes:
        # Count sentiment of high-confidence quotes
        quote_sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        for q in high_conf_quotes:
            sent = q.get("sentiment", "neutral")
            quote_sentiments[sent] = quote_sentiments.get(sent, 0) + 1

        if quote_sentiments[dominant_sentiment] >= len(high_conf_quotes) * 0.5:
            factors.append({
                "type": "high_confidence_quotes",
                "description": f"High-confidence quotes predominantly {dominant_sentiment}",
                "impact": dominant_sentiment if dominant_sentiment != "neutral" else "neutral",
            })

    # Factor 4: Sample size consideration
    if post_count >= 50:
        factors.append({
            "type": "sample_size",
            "description": f"Analysis based on {post_count} posts provides reliable signal",
            "impact": "neutral",
        })
    elif post_count < 10:
        factors.append({
            "type": "limited_sample",
            "description": f"Limited sample size ({post_count} posts) may affect accuracy",
            "impact": "neutral",
        })

    # Generate primary reason
    primary_reason = _generate_primary_reason(
        dominant_sentiment, strength, source_mix, post_count
    )

    # Generate distribution note
    if strength == "strong":
        distribution_note = f"{dominant_value:.0f}% {dominant_sentiment} indicates clear community consensus"
    elif strength == "moderate":
        distribution_note = f"{dominant_value:.0f}% {dominant_sentiment} shows a notable trend"
    else:
        distribution_note = "Close sentiment split suggests varied community opinions"

    return {
        "dominant_sentiment": dominant_sentiment,
        "strength": strength,
        "primary_reason": primary_reason,
        "factors": factors,
        "sentiment_distribution_note": distribution_note,
    }


def generate_confidence_breakdown(
    post_count: int,
    source_mix: dict[str, int],
    quotes: list[dict],
    sentiment_positive: float,
    sentiment_neutral: float,
    sentiment_negative: float,
) -> dict[str, Any]:
    """Generate detailed confidence score breakdown with contributing factors.

    Scores four weighted factors to produce overall confidence and explanations.

    Args:
        post_count: Total number of posts analyzed.
        source_mix: Dict mapping platform names to post counts.
        quotes: List of representative quote dicts with confidence scores.
        sentiment_positive: Positive sentiment percentage (0-100).
        sentiment_neutral: Neutral sentiment percentage (0-100).
        sentiment_negative: Negative sentiment percentage (0-100).

    Returns:
        Dict containing overall score, level, factors, and limitations.
    """
    factors = []
    limitations = []

    # Factor 1: Sample Size (30% weight)
    sample_score = _score_sample_size(post_count)
    sample_explanation = _explain_sample_size(post_count)
    factors.append({
        "name": "Sample Size",
        "score": sample_score,
        "weight": 0.30,
        "explanation": sample_explanation,
    })
    if sample_score < 0.5:
        limitations.append("Limited sample size may affect accuracy")

    # Factor 2: Source Diversity (20% weight)
    diversity_score = _score_source_diversity(source_mix)
    diversity_explanation = _explain_source_diversity(source_mix)
    factors.append({
        "name": "Source Diversity",
        "score": diversity_score,
        "weight": 0.20,
        "explanation": diversity_explanation,
    })
    if diversity_score < 0.5:
        limitations.append("Limited source variety may create bias")

    # Factor 3: Model Confidence (30% weight)
    model_score = _score_model_confidence(quotes)
    model_explanation = _explain_model_confidence(quotes)
    factors.append({
        "name": "Model Confidence",
        "score": model_score,
        "weight": 0.30,
        "explanation": model_explanation,
    })
    if model_score < 0.5:
        limitations.append("NLP model showed lower confidence in classifications")

    # Factor 4: Sentiment Agreement (20% weight)
    agreement_score = _score_sentiment_agreement(
        sentiment_positive, sentiment_neutral, sentiment_negative
    )
    agreement_explanation = _explain_sentiment_agreement(
        sentiment_positive, sentiment_neutral, sentiment_negative
    )
    factors.append({
        "name": "Sentiment Agreement",
        "score": agreement_score,
        "weight": 0.20,
        "explanation": agreement_explanation,
    })
    if agreement_score < 0.5:
        limitations.append("Mixed sentiment suggests topic may be controversial")

    # Calculate weighted overall score
    overall_score = sum(f["score"] * f["weight"] for f in factors)

    # Determine confidence level
    if overall_score >= 0.7:
        level = "high"
    elif overall_score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return {
        "overall_score": round(overall_score, 2),
        "level": level,
        "factors": factors,
        "limitations": limitations if limitations else None,
    }


def _analyze_platform_sentiment(quotes: list[dict]) -> dict[str, dict[str, int]]:
    """Analyze sentiment distribution per platform from quotes."""
    platform_sentiments: dict[str, dict[str, int]] = {}

    for quote in quotes:
        platform = quote.get("platform", "unknown")
        sentiment = quote.get("sentiment", "neutral")

        if platform not in platform_sentiments:
            platform_sentiments[platform] = {"positive": 0, "neutral": 0, "negative": 0}

        platform_sentiments[platform][sentiment] = platform_sentiments[platform].get(sentiment, 0) + 1

    return platform_sentiments


def _check_consensus(platform_sentiments: dict[str, dict[str, int]], dominant: str) -> bool:
    """Check if majority of platforms agree on dominant sentiment."""
    if not platform_sentiments:
        return True

    agreeing_platforms = 0
    for platform, sentiments in platform_sentiments.items():
        platform_dominant = max(sentiments, key=sentiments.get)
        if platform_dominant == dominant:
            agreeing_platforms += 1

    return agreeing_platforms >= len(platform_sentiments) * 0.6


def _generate_primary_reason(
    dominant: str, strength: str, source_mix: dict[str, int], post_count: int
) -> str:
    """Generate the primary reason statement."""
    # Find top source
    top_source = max(source_mix, key=source_mix.get) if source_mix else "community"
    top_source_display = _format_platform_name(top_source)

    if strength == "strong":
        if dominant == "positive":
            return f"Strong positive reception from {top_source_display} contributors"
        elif dominant == "negative":
            return f"Significant criticism voiced by {top_source_display} contributors"
        else:
            return f"Neutral discussion from {top_source_display} contributors"
    elif strength == "moderate":
        if dominant == "positive":
            return f"Generally positive feedback with some mixed opinions"
        elif dominant == "negative":
            return f"Notable concerns raised alongside some positive feedback"
        else:
            return f"Balanced discussion with varied perspectives"
    else:
        return f"Divided opinions across the community"


def _format_platform_name(platform: str) -> str:
    """Format platform name for display."""
    platform_names = {
        "youtube": "YouTube",
        "official-news": "OfficialNews",
        "tier-site": "TierSite",
        "guide-site": "GuideSite",
        "google_trends": "Google Trends",
    }
    return platform_names.get(platform, platform.title())


def _score_sample_size(post_count: int) -> float:
    """Score sample size factor (0-1)."""
    if post_count >= 100:
        return 1.0
    elif post_count >= 50:
        return 0.85
    elif post_count >= 25:
        return 0.7
    elif post_count >= 10:
        return 0.5
    elif post_count >= 5:
        return 0.3
    else:
        return 0.15


def _explain_sample_size(post_count: int) -> str:
    """Generate explanation for sample size score."""
    if post_count >= 100:
        return f"Excellent sample: {post_count} posts analyzed"
    elif post_count >= 50:
        return f"Good sample: {post_count} posts analyzed"
    elif post_count >= 25:
        return f"Moderate sample: {post_count} posts analyzed"
    elif post_count >= 10:
        return f"Limited sample: {post_count} posts analyzed"
    else:
        return f"Very small sample: only {post_count} posts analyzed"


def _score_source_diversity(source_mix: dict[str, int]) -> float:
    """Score source diversity factor (0-1)."""
    platform_count = len(source_mix)

    if platform_count == 0:
        return 0.0

    total_posts = sum(source_mix.values())
    if total_posts == 0:
        return 0.0

    # Base score from platform count
    if platform_count >= 4:
        base = 0.8
    elif platform_count >= 3:
        base = 0.6
    elif platform_count >= 2:
        base = 0.4
    else:
        base = 0.2

    # Bonus for balanced distribution (max 0.2)
    max_share = max(source_mix.values()) / total_posts
    balance_bonus = 0.2 * (1 - max_share)

    return min(1.0, base + balance_bonus)


def _explain_source_diversity(source_mix: dict[str, int]) -> str:
    """Generate explanation for source diversity score."""
    platform_count = len(source_mix)
    total = sum(source_mix.values()) if source_mix else 0

    if platform_count >= 3:
        return f"Data from {platform_count} different platforms"
    elif platform_count == 2:
        platforms = list(source_mix.keys())
        return f"Data from {_format_platform_name(platforms[0])} and {_format_platform_name(platforms[1])}"
    elif platform_count == 1:
        platform = list(source_mix.keys())[0]
        return f"Data from {_format_platform_name(platform)} only"
    else:
        return "No source data available"


def _score_model_confidence(quotes: list[dict]) -> float:
    """Score model confidence factor (0-1) based on quote confidence scores."""
    if not quotes:
        return 0.5  # Neutral if no quotes

    confidences = [q.get("confidence", 0.5) for q in quotes]
    avg_confidence = sum(confidences) / len(confidences)

    return avg_confidence


def _explain_model_confidence(quotes: list[dict]) -> str:
    """Generate explanation for model confidence score."""
    if not quotes:
        return "No high-confidence quotes available"

    confidences = [q.get("confidence", 0.5) for q in quotes]
    avg_confidence = sum(confidences) / len(confidences)

    if avg_confidence >= 0.85:
        return "NLP model highly confident in sentiment classifications"
    elif avg_confidence >= 0.7:
        return "NLP model showed good confidence in most classifications"
    elif avg_confidence >= 0.5:
        return "NLP model had moderate confidence in classifications"
    else:
        return "NLP model was uncertain about some classifications"


def _score_sentiment_agreement(positive: float, neutral: float, negative: float) -> float:
    """Score sentiment agreement factor (0-1) based on distribution spread."""
    values = sorted([positive, neutral, negative], reverse=True)

    # Higher score when one sentiment clearly dominates
    dominance = values[0]
    spread = values[0] - values[1]  # Gap between top two

    if dominance >= 60 and spread >= 30:
        return 1.0
    elif dominance >= 50 and spread >= 20:
        return 0.8
    elif dominance >= 40 and spread >= 10:
        return 0.6
    elif dominance >= 35:
        return 0.4
    else:
        return 0.25


def _explain_sentiment_agreement(positive: float, neutral: float, negative: float) -> str:
    """Generate explanation for sentiment agreement score."""
    values = {"positive": positive, "neutral": neutral, "negative": negative}
    dominant = max(values, key=values.get)
    dominant_pct = values[dominant]

    if dominant_pct >= 60:
        return f"Strong consensus: {dominant_pct:.0f}% {dominant}"
    elif dominant_pct >= 45:
        return f"Clear trend: {dominant_pct:.0f}% {dominant}"
    else:
        return f"Mixed opinions: no clear majority"
