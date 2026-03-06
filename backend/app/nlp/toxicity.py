"""Toxicity detection using Detoxify model."""

import logging
from dataclasses import dataclass

import torch
from detoxify import Detoxify

from app.nlp.models import get_device, clear_cuda_cache

logger = logging.getLogger(__name__)

# Model variant - 'original' has 98.64% AUC on Jigsaw dataset
MODEL_VARIANT = "original"

# Higher threshold for gaming content to reduce false positives
# on terms like "kill", "destroy", "flame"
DEFAULT_THRESHOLD = 0.7


@dataclass
class ToxicityResult:
    """Result from toxicity detection."""

    is_toxic: bool  # toxicity_score > threshold
    toxicity_score: float  # Main toxicity score 0.0-1.0
    categories: dict[str, float]  # All 6 category scores


class ToxicityDetector:
    """Detoxify-based toxicity detector for text content.

    Uses the 'original' Detoxify model trained on Jigsaw toxic comment
    data with 98.64% AUC. Provides scores for 6 categories:
    toxicity, severe_toxicity, obscene, threat, insult, identity_hate.

    Uses a higher threshold (0.7) than default to reduce false positives
    on gaming terminology like "kill", "flame", "destroy".
    """

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, batch_size: int = 32):
        """Initialize toxicity detector.

        Args:
            threshold: Score threshold for marking content as toxic.
            batch_size: Number of texts to process per batch.
        """
        self.threshold = threshold
        self.batch_size = batch_size
        self._model = None

    def _ensure_loaded(self) -> None:
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info("Loading toxicity model: detoxify/%s", MODEL_VARIANT)
            device = get_device()
            self._model = Detoxify(MODEL_VARIANT, device=device)
            logger.info("Toxicity model loaded successfully (device=%s)", device)

    def detect(self, text: str) -> ToxicityResult:
        """Detect toxicity in a single text.

        Args:
            text: Text to analyze.

        Returns:
            ToxicityResult with is_toxic flag, score, and categories.
        """
        results = self.detect_batch([text])
        return results[0]

    def detect_batch(self, texts: list[str]) -> list[ToxicityResult]:
        """Detect toxicity in multiple texts.

        Args:
            texts: List of texts to analyze.

        Returns:
            List of ToxicityResult objects in same order as input.
        """
        if not texts:
            return []

        self._ensure_loaded()

        # Preprocess: handle empty strings
        processed_texts = [t if t and t.strip() else "neutral" for t in texts]

        results: list[ToxicityResult] = []

        with torch.no_grad():
            # Process in batches
            for i in range(0, len(processed_texts), self.batch_size):
                batch = processed_texts[i : i + self.batch_size]

                try:
                    # Detoxify returns dict with category names as keys
                    # and lists of scores as values
                    predictions = self._model.predict(batch)

                    # predictions format:
                    # {"toxicity": [0.1, 0.2], "severe_toxicity": [0.01, 0.02], ...}
                    # Note: different model versions may have different keys
                    batch_size = len(batch)
                    for j in range(batch_size):
                        # Build categories dict from available keys
                        categories = {}
                        for key in ["toxicity", "severe_toxicity", "obscene",
                                    "threat", "insult", "identity_hate", "identity_attack"]:
                            if key in predictions:
                                categories[key] = float(predictions[key][j])

                        # Ensure we have at least a toxicity score
                        toxicity_score = categories.get("toxicity", 0.0)
                        is_toxic = toxicity_score > self.threshold

                        results.append(
                            ToxicityResult(
                                is_toxic=is_toxic,
                                toxicity_score=toxicity_score,
                                categories=categories,
                            )
                        )

                except Exception as e:
                    logger.error("Batch toxicity detection failed: %s", e)
                    # Return non-toxic for failed batch
                    for _ in batch:
                        results.append(
                            ToxicityResult(
                                is_toxic=False,
                                toxicity_score=0.0,
                                categories={
                                    "toxicity": 0.0,
                                    "severe_toxicity": 0.0,
                                    "obscene": 0.0,
                                    "threat": 0.0,
                                    "insult": 0.0,
                                    "identity_hate": 0.0,
                                },
                            )
                        )

                # Clear GPU memory between batches
                clear_cuda_cache()

        return results

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return f"detoxify/{MODEL_VARIANT}"
