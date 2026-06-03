"""Evaluation service — orchestrates evaluation, regression, and drift detection."""

from __future__ import annotations

import structlog

from voice_orchestrator.domain.interfaces.repositories import (
    ExtractionRepository,
    FeedbackRepository,
    GoldenSampleRepository,
)
from voice_orchestrator.domain.models.core import Action, FeedbackStatus
from voice_orchestrator.evaluation.drift import DriftDetector
from voice_orchestrator.evaluation.metrics import (
    ExtractionMetrics,
    compute_extraction_metrics,
)

logger = structlog.get_logger(__name__)


class EvaluationService:
    def __init__(
        self,
        extraction_repo: ExtractionRepository,
        feedback_repo: FeedbackRepository,
        golden_repo: GoldenSampleRepository,
    ):
        self._extraction_repo = extraction_repo
        self._feedback_repo = feedback_repo
        self._golden_repo = golden_repo
        self._drift_detector = DriftDetector()

    async def evaluate_extraction(
        self,
        extraction_id: str,
        expected_actions: list[Action],
    ) -> ExtractionMetrics:
        extraction = await self._extraction_repo.get_by_id(extraction_id)
        if not extraction:
            raise ValueError(f"Extraction not found: {extraction_id}")

        metrics = compute_extraction_metrics(expected_actions, extraction.actions)

        logger.info(
            "evaluation_complete",
            extraction_id=extraction_id,
            intent_accuracy=metrics.intent_accuracy,
            entity_f1=metrics.entity_f1,
        )

        return metrics

    async def compute_quality_report(self) -> dict:
        """Compare AI output against human corrections."""
        corrected = await self._feedback_repo.list_by_status(FeedbackStatus.CORRECTED, 10000)

        if not corrected:
            return {"total_corrections": 0, "avg_intent_accuracy": 0.0, "avg_entity_f1": 0.0}

        total_intent_acc = 0.0
        total_entity_f1 = 0.0
        count = 0

        for fb in corrected:
            if not fb.corrected_actions:
                continue

            extraction = await self._extraction_repo.get_by_id(fb.extraction_id)
            if not extraction:
                continue

            metrics = compute_extraction_metrics(fb.corrected_actions, extraction.actions)
            total_intent_acc += metrics.intent_accuracy
            total_entity_f1 += metrics.entity_f1
            count += 1

        n = count or 1
        return {
            "total_corrections": count,
            "avg_intent_accuracy": total_intent_acc / n,
            "avg_entity_f1": total_entity_f1 / n,
        }
