"""Feedback service — human review loop for AI output correction."""

from __future__ import annotations

from typing import Any

import structlog

from voice_orchestrator.domain.interfaces.repositories import (
    ExtractionRepository,
    FeedbackRepository,
)
from voice_orchestrator.domain.models.core import Action, Feedback, FeedbackStatus

logger = structlog.get_logger(__name__)


class FeedbackService:
    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        extraction_repo: ExtractionRepository,
    ):
        self._feedback_repo = feedback_repo
        self._extraction_repo = extraction_repo

    async def submit(
        self,
        extraction_id: str,
        status: FeedbackStatus,
        corrected_actions: list[Action] | None = None,
        reviewer: str | None = None,
        notes: str | None = None,
    ) -> Feedback:
        extraction = await self._extraction_repo.get_by_id(extraction_id)
        if not extraction:
            raise ValueError(f"Extraction not found: {extraction_id}")

        feedback = Feedback(
            extraction_id=extraction_id,
            status=status,
            corrected_actions=corrected_actions,
            reviewer=reviewer,
            notes=notes,
        )

        saved = await self._feedback_repo.save(feedback)

        logger.info(
            "feedback_submitted",
            feedback_id=saved.id,
            extraction_id=extraction_id,
            status=status,
        )

        return saved

    async def get_review_queue(self, limit: int = 50) -> list[Feedback]:
        return await self._feedback_repo.list_by_status(FeedbackStatus.PENDING, limit)

    async def get_by_extraction(self, extraction_id: str) -> Feedback | None:
        return await self._feedback_repo.get_by_extraction_id(extraction_id)

    async def compute_agreement_rate(self) -> dict[str, Any]:
        approved = await self._feedback_repo.list_by_status(FeedbackStatus.APPROVED, 10000)
        rejected = await self._feedback_repo.list_by_status(FeedbackStatus.REJECTED, 10000)
        corrected = await self._feedback_repo.list_by_status(FeedbackStatus.CORRECTED, 10000)

        total = len(approved) + len(rejected) + len(corrected)
        if total == 0:
            return {"agreement_rate": 0.0, "total_reviewed": 0}

        return {
            "agreement_rate": len(approved) / total,
            "total_reviewed": total,
            "approved": len(approved),
            "rejected": len(rejected),
            "corrected": len(corrected),
        }
