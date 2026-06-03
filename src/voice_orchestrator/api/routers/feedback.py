"""Feedback router — human review loop."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from voice_orchestrator.api.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Submit feedback on an extraction result."""
    raise HTTPException(status_code=501, detail="Requires DB connection")


@router.get("/queue", response_model=list[FeedbackResponse])
async def get_review_queue(limit: int = 50) -> list[FeedbackResponse]:
    """Get pending feedback items for review."""
    return []
