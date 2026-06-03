"""Evaluation router — evaluate extractions and get metrics."""

from __future__ import annotations

from fastapi import APIRouter

from voice_orchestrator.api.schemas import (
    EvaluateRequest,
    EvaluationResponse,
    MetricsResponse,
    ProviderCompareResponse,
)

router = APIRouter(tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluateRequest) -> EvaluationResponse:
    """Evaluate an extraction against expected actions."""
    # Placeholder — in production, this pulls from DB
    return EvaluationResponse(
        extraction_id=request.extraction_id,
        intent_accuracy=0.0,
        entity_precision=0.0,
        entity_recall=0.0,
        entity_f1=0.0,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get pipeline production metrics."""
    return MetricsResponse()


@router.get("/providers/compare", response_model=ProviderCompareResponse)
async def compare_providers() -> ProviderCompareResponse:
    """Compare performance across STT and LLM providers."""
    return ProviderCompareResponse(results=[])
