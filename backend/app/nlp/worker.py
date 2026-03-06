"""Standalone NLP worker process.

Runs as a separate container/process to isolate ML models from the main API.
Provides REST API for NLP operations.
"""

import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.nlp.sentiment import SentimentAnalyzer, SentimentScore
from app.nlp.topics import TopicDetector, TopicResult
from app.nlp.toxicity import ToxicityDetector, ToxicityResult
from app.nlp.health import get_memory_usage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global model instances (loaded once at startup)
_sentiment_analyzer: SentimentAnalyzer | None = None
_topic_detector: TopicDetector | None = None
_toxicity_detector: ToxicityDetector | None = None
_models_loaded = False


class AnalyzeRequest(BaseModel):
    """Request body for batch analysis."""

    texts: list[str] = Field(..., min_length=1, max_length=1000)


class SentimentResultSchema(BaseModel):
    """Sentiment analysis result."""

    label: str
    confidence: float
    scores: dict[str, float]


class TopicResultSchema(BaseModel):
    """Topic detection result."""

    primary_topic: str
    all_topics: list[str]
    confidence: dict[str, float] | None = None


class ToxicityResultSchema(BaseModel):
    """Toxicity detection result."""

    is_toxic: bool
    toxicity_score: float
    categories: dict[str, float]


class AnalyzeResponse(BaseModel):
    """Response for batch analysis."""

    sentiment: list[SentimentResultSchema]
    topics: list[TopicResultSchema]
    toxicity: list[ToxicityResultSchema]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    models_loaded: bool
    memory: dict[str, Any]


def load_models() -> None:
    """Load all NLP models into memory."""
    global _sentiment_analyzer, _topic_detector, _toxicity_detector, _models_loaded

    batch_size = int(os.environ.get("NLP_BATCH_SIZE", "32"))

    logger.info("Loading NLP models...")

    try:
        logger.info("Loading sentiment analyzer...")
        _sentiment_analyzer = SentimentAnalyzer(batch_size=batch_size)

        logger.info("Loading topic detector...")
        _topic_detector = TopicDetector(batch_size=batch_size)

        logger.info("Loading toxicity detector...")
        _toxicity_detector = ToxicityDetector(batch_size=batch_size)

        _models_loaded = True
        logger.info("All models loaded successfully")

    except Exception as e:
        logger.error("Failed to load models: %s", e)
        _models_loaded = False
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Load models on startup
    try:
        load_models()
    except Exception as e:
        logger.error("Failed to initialize models: %s", e)
        # Don't exit - allow container to report unhealthy

    yield

    # Cleanup
    logger.info("NLP worker shutting down")


app = FastAPI(
    title="CommunityPulse NLP Worker",
    description="Isolated NLP processing worker",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    """Readiness probe - returns 200 only if models are loaded.

    Used by Kubernetes/Docker health checks.
    """
    memory = get_memory_usage()

    if not _models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    return HealthResponse(
        status="ready",
        models_loaded=True,
        memory=memory,
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe - returns 200 if process is alive."""
    memory = get_memory_usage()

    return HealthResponse(
        status="alive" if _models_loaded else "loading",
        models_loaded=_models_loaded,
        memory=memory,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run full NLP analysis on batch of texts.

    Args:
        request: Batch of texts to analyze.

    Returns:
        Sentiment, topic, and toxicity results for each text.

    Raises:
        HTTPException: If models not loaded or analysis fails.
    """
    if not _models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    if (
        _sentiment_analyzer is None
        or _topic_detector is None
        or _toxicity_detector is None
    ):
        raise HTTPException(status_code=503, detail="Models not initialized")

    texts = request.texts
    logger.info("Analyzing batch of %d texts", len(texts))

    try:
        # Run analysis
        sentiment_results = _sentiment_analyzer.analyze_batch(texts)
        topic_results = _topic_detector.detect_batch(texts)
        toxicity_results = _toxicity_detector.detect_batch(texts)

        # Convert to response schemas
        sentiment_response = [
            SentimentResultSchema(
                label=r.label,
                confidence=r.confidence,
                scores=r.scores,
            )
            for r in sentiment_results
        ]

        topics_response = [
            TopicResultSchema(
                primary_topic=r.topics[0] if r.topics else "uncategorized",
                all_topics=r.topics,
                confidence=dict(zip(r.topics, r.probabilities)) if r.topics and r.probabilities else None,
            )
            for r in topic_results
        ]

        toxicity_response = [
            ToxicityResultSchema(
                is_toxic=r.is_toxic,
                toxicity_score=r.toxicity_score,
                categories=r.categories,
            )
            for r in toxicity_results
        ]

        return AnalyzeResponse(
            sentiment=sentiment_response,
            topics=topics_response,
            toxicity=toxicity_response,
        )

    except Exception as e:
        logger.error("Analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


def handle_signal(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d, shutting down...", signum)
    sys.exit(0)


def main() -> None:
    """Entry point for NLP worker."""
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    host = os.environ.get("NLP_WORKER_HOST", "0.0.0.0")
    port = int(os.environ.get("NLP_WORKER_PORT", "8001"))

    logger.info("Starting NLP worker on %s:%d", host, port)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
