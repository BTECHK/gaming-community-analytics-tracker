"""Device detection and CUDA utilities for NLP models."""

import logging

import torch

logger = logging.getLogger(__name__)


def get_device() -> str:
    """Get the best available device for inference.

    Returns:
        "cuda" if GPU available, "cpu" otherwise.
    """
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        logger.info("Using CUDA device: %s", device_name)
        return "cuda"
    logger.info("CUDA not available, using CPU")
    return "cpu"


def get_device_id() -> int:
    """Get device ID for transformers pipeline.

    Returns:
        0 for GPU (first CUDA device), -1 for CPU.
    """
    return 0 if torch.cuda.is_available() else -1


def clear_cuda_cache() -> None:
    """Free GPU memory between batches.

    Should be called after processing large batches to prevent
    memory fragmentation on long-running processes.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.debug("CUDA cache cleared")
