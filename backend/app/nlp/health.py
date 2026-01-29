"""NLP health check utilities."""

import logging
import os
import psutil
from typing import Any

import httpx

from app.config import get_settings
from app.nlp.circuit_breaker import get_all_breaker_statuses
from app.nlp.jobs import get_job_manager
from app.nlp.dead_letter import DeadLetterQueue

logger = logging.getLogger(__name__)


def get_memory_usage() -> dict[str, Any]:
    """Get current memory usage statistics.

    Returns:
        Dict with memory information.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    virtual_mem = psutil.virtual_memory()

    return {
        "process_rss_mb": round(mem_info.rss / 1024 / 1024, 2),
        "process_vms_mb": round(mem_info.vms / 1024 / 1024, 2),
        "system_total_mb": round(virtual_mem.total / 1024 / 1024, 2),
        "system_available_mb": round(virtual_mem.available / 1024 / 1024, 2),
        "system_percent_used": virtual_mem.percent,
    }


def check_model_status() -> dict[str, Any]:
    """Check if NLP models are loaded and functional.

    Returns:
        Dict with model status information.
    """
    models_status = {
        "sentiment": {"loaded": False, "error": None},
        "topics": {"loaded": False, "error": None},
        "toxicity": {"loaded": False, "error": None},
    }

    # Check sentiment model
    try:
        from app.nlp.sentiment import SentimentAnalyzer

        analyzer = SentimentAnalyzer(batch_size=1)
        # Quick test with minimal input
        result = analyzer.analyze_batch(["test"])
        if result:
            models_status["sentiment"]["loaded"] = True
    except Exception as e:
        models_status["sentiment"]["error"] = str(e)
        logger.warning("Sentiment model check failed: %s", e)

    # Check topic model
    try:
        from app.nlp.topics import TopicDetector

        detector = TopicDetector(batch_size=1)
        result = detector.detect_batch(["test"])
        if result:
            models_status["topics"]["loaded"] = True
    except Exception as e:
        models_status["topics"]["error"] = str(e)
        logger.warning("Topic model check failed: %s", e)

    # Check toxicity model
    try:
        from app.nlp.toxicity import ToxicityDetector

        detector = ToxicityDetector(batch_size=1)
        result = detector.detect_batch(["test"])
        if result:
            models_status["toxicity"]["loaded"] = True
    except Exception as e:
        models_status["toxicity"]["error"] = str(e)
        logger.warning("Toxicity model check failed: %s", e)

    return models_status


async def get_dlq_stats() -> dict[str, Any] | None:
    """Get dead letter queue statistics.

    Returns:
        DLQ stats or None if unavailable.
    """
    try:
        dlq = await DeadLetterQueue.get_instance()
        return await dlq.get_stats()
    except Exception as e:
        logger.warning("Failed to get DLQ stats: %s", e)
        return None


async def check_worker_status() -> dict[str, Any]:
    """Check NLP worker availability and status.

    Returns:
        Dict with worker status information.
    """
    settings = get_settings()

    if not settings.nlp_use_worker:
        return {
            "enabled": False,
            "available": False,
            "url": settings.nlp_worker_url,
            "error": "Worker disabled in settings",
        }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.nlp_worker_url}/ready")
            if response.status_code == 200:
                data = response.json()
                return {
                    "enabled": True,
                    "available": True,
                    "url": settings.nlp_worker_url,
                    "memory": data.get("memory"),
                    "models_loaded": data.get("models_loaded", False),
                }
            else:
                return {
                    "enabled": True,
                    "available": False,
                    "url": settings.nlp_worker_url,
                    "error": f"Worker returned status {response.status_code}",
                }
    except Exception as e:
        return {
            "enabled": True,
            "available": False,
            "url": settings.nlp_worker_url,
            "error": str(e),
        }


async def get_nlp_health() -> dict[str, Any]:
    """Get comprehensive NLP system health.

    Returns:
        Dict with full health information.
    """
    memory = get_memory_usage()

    # Determine overall health based on memory
    memory_healthy = memory["system_percent_used"] < 90 and memory["process_rss_mb"] < 4000

    # Get circuit breaker states
    circuit_breakers = get_all_breaker_statuses()
    circuits_healthy = all(
        cb["state"] != "open" for cb in circuit_breakers
    )

    # Get job status
    job_manager = get_job_manager()
    job_status = await job_manager.get_status()

    # Get DLQ stats
    dlq_stats = await get_dlq_stats()
    dlq_healthy = dlq_stats is None or dlq_stats.get("exhausted", 0) == 0

    # Get worker status
    worker_status = await check_worker_status()
    worker_available = worker_status.get("available", False)

    # Overall status
    overall_healthy = memory_healthy and circuits_healthy and dlq_healthy

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "memory": memory,
        "memory_healthy": memory_healthy,
        "circuit_breakers": circuit_breakers,
        "circuits_healthy": circuits_healthy,
        "job": job_status,
        "dlq": dlq_stats,
        "dlq_healthy": dlq_healthy,
        "worker": worker_status,
        "worker_available": worker_available,
    }


async def get_nlp_health_detailed() -> dict[str, Any]:
    """Get detailed NLP health including model checks.

    This is more expensive as it tests model loading.

    Returns:
        Dict with detailed health information.
    """
    health = await get_nlp_health()

    # Add model status (expensive check)
    models = check_model_status()
    models_healthy = all(m["loaded"] for m in models.values())

    health["models"] = models
    health["models_healthy"] = models_healthy

    # Update overall status including DLQ
    health["status"] = (
        "healthy"
        if (
            health["memory_healthy"]
            and health["circuits_healthy"]
            and health["dlq_healthy"]
            and models_healthy
        )
        else "degraded"
    )

    return health
