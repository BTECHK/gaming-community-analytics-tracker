"""Sentiment analysis using RoBERTa model trained on tweets."""

import logging
from dataclasses import dataclass

import torch
from transformers import pipeline

from app.nlp.models import get_device_id, clear_cuda_cache

logger = logging.getLogger(__name__)

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Map model labels to our enum values (lowercase)
LABEL_MAP = {
    "Positive": "positive",
    "Neutral": "neutral",
    "Negative": "negative",
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}


@dataclass
class SentimentScore:
    """Result from sentiment analysis."""

    label: str  # "positive", "neutral", "negative"
    confidence: float  # Confidence score for the predicted label
    scores: dict[str, float]  # All class scores {"positive": 0.8, "neutral": 0.15, "negative": 0.05}


class SentimentAnalyzer:
    """RoBERTa-based sentiment analyzer for text content.

    Uses cardiffnlp/twitter-roberta-base-sentiment-latest which was
    trained on ~124M tweets and performs well on informal text.

    The model is loaded once at initialization to avoid cold start
    latency on each request.
    """

    def __init__(self, batch_size: int = 32):
        """Initialize sentiment analyzer.

        Args:
            batch_size: Number of texts to process per batch.
        """
        self.batch_size = batch_size
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        """Lazy load the model on first use."""
        if self._pipeline is None:
            logger.info("Loading sentiment model: %s", MODEL_NAME)
            device_id = get_device_id()
            self._pipeline = pipeline(
                "sentiment-analysis",
                model=MODEL_NAME,
                device=device_id,
                top_k=None,  # Get all class scores
                truncation=True,
                max_length=512,
            )
            logger.info("Sentiment model loaded successfully (device=%d)", device_id)

    def analyze(self, text: str) -> SentimentScore:
        """Analyze sentiment of a single text.

        Args:
            text: Text to analyze.

        Returns:
            SentimentScore with label, confidence, and all scores.
        """
        results = self.analyze_batch([text])
        return results[0]

    def analyze_batch(self, texts: list[str]) -> list[SentimentScore]:
        """Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze.

        Returns:
            List of SentimentScore objects in same order as input.
        """
        if not texts:
            return []

        self._ensure_loaded()

        # Preprocess: handle empty strings
        processed_texts = [t if t and t.strip() else "neutral" for t in texts]

        results: list[SentimentScore] = []

        with torch.no_grad():
            # Process in batches
            for i in range(0, len(processed_texts), self.batch_size):
                batch = processed_texts[i : i + self.batch_size]

                try:
                    batch_results = self._pipeline(batch)

                    for item in batch_results:
                        # item is a list of dicts: [{"label": "Positive", "score": 0.8}, ...]
                        scores = {
                            LABEL_MAP.get(d["label"], d["label"].lower()): d["score"]
                            for d in item
                        }

                        # Find highest scoring label
                        best = max(item, key=lambda x: x["score"])
                        label = LABEL_MAP.get(best["label"], best["label"].lower())

                        results.append(
                            SentimentScore(
                                label=label,
                                confidence=best["score"],
                                scores=scores,
                            )
                        )
                except Exception as e:
                    logger.error("Batch sentiment analysis failed: %s", e)
                    # Return neutral for failed batch
                    for _ in batch:
                        results.append(
                            SentimentScore(
                                label="neutral",
                                confidence=0.0,
                                scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                            )
                        )

                # Clear GPU memory between batches
                clear_cuda_cache()

        return results

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return MODEL_NAME
