"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Placeholder health check - will be enhanced in Task 2."""
    return {"status": "healthy"}
