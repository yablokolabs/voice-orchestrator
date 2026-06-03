"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter

from voice_orchestrator.api.schemas import HealthResponse
from voice_orchestrator.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
    )
