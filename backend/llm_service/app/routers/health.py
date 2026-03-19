"""Health check endpoints."""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request):
    builder = getattr(request.app.state, "sentence_builder", None)
    healthy = builder.is_healthy() if builder else False

    return {
        "status": "healthy" if healthy else "degraded",
        "service": "llm_service",
        "timestamp": datetime.now(UTC).isoformat(),
        "gemini_api": "up" if healthy else "down",
    }


@router.get("/api/v1/health")
async def health_check_v1(request: Request):
    return await health_check(request)
