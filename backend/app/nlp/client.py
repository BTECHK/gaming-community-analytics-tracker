"""Client for calling the NLP worker service.

Used by the main API server to delegate NLP processing to the isolated worker.
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel

from app.nlp.sentiment import SentimentScore
from app.nlp.topics import TopicResult
from app.nlp.toxicity import ToxicityResult

logger = logging.getLogger(__name__)


class NLPWorkerClient:
    """HTTP client for NLP worker service.

    Handles communication with the isolated NLP worker container.
    Includes timeout handling, retry logic, and graceful degradation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize NLP worker client.

        Args:
            base_url: Worker URL. Defaults to NLP_WORKER_URL env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
        """
        self.base_url = base_url or os.environ.get(
            "NLP_WORKER_URL", "http://nlp-worker:8001"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def is_ready(self) -> bool:
        """Check if worker is ready to accept requests.

        Returns:
            True if worker is ready, False otherwise.
        """
        try:
            client = await self._get_client()
            response = await client.get("/ready", timeout=10.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug("Worker readiness check failed: %s", e)
            return False

    async def get_health(self) -> dict[str, Any]:
        """Get worker health status.

        Returns:
            Health status dict or error dict.
        """
        try:
            client = await self._get_client()
            response = await client.get("/health", timeout=10.0)
            return response.json()
        except Exception as e:
            logger.warning("Worker health check failed: %s", e)
            return {"status": "unavailable", "error": str(e)}

    async def analyze_batch(
        self,
        texts: list[str],
    ) -> tuple[list[SentimentScore], list[TopicResult], list[ToxicityResult]] | None:
        """Send texts to worker for analysis.

        Args:
            texts: List of texts to analyze.

        Returns:
            Tuple of (sentiment, topics, toxicity) results, or None if failed.
        """
        if not texts:
            return [], [], []

        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    "/analyze",
                    json={"texts": texts},
                )
                response.raise_for_status()
                data = response.json()

                # Convert response to internal types
                sentiment_results = [
                    SentimentScore(
                        label=s["label"],
                        confidence=s["confidence"],
                        scores=s["scores"],
                    )
                    for s in data["sentiment"]
                ]

                topic_results = [
                    TopicResult(
                        primary_topic=t["primary_topic"],
                        all_topics=t["all_topics"],
                        confidence=t["confidence"],
                    )
                    for t in data["topics"]
                ]

                toxicity_results = [
                    ToxicityResult(
                        is_toxic=t["is_toxic"],
                        toxicity_score=t["toxicity_score"],
                        categories=t["categories"],
                    )
                    for t in data["toxicity"]
                ]

                return sentiment_results, topic_results, toxicity_results

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Worker request timed out (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 503:
                    logger.warning(
                        "Worker not ready (attempt %d/%d): %s",
                        attempt + 1,
                        self.max_retries,
                        e,
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(5)
                else:
                    logger.error("Worker request failed: %s", e)
                    break

            except Exception as e:
                last_error = e
                logger.error("Unexpected error calling worker: %s", e)
                break

        logger.error(
            "Failed to analyze batch after %d attempts: %s",
            self.max_retries,
            last_error,
        )
        return None


# Global client instance
_worker_client: NLPWorkerClient | None = None


def get_worker_client() -> NLPWorkerClient:
    """Get the global NLP worker client instance."""
    global _worker_client
    if _worker_client is None:
        _worker_client = NLPWorkerClient()
    return _worker_client


async def is_worker_available() -> bool:
    """Check if the NLP worker is available.

    Returns:
        True if worker is ready, False otherwise.
    """
    client = get_worker_client()
    return await client.is_ready()
