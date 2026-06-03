"""Regression framework — run golden dataset against pipeline configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from voice_orchestrator.domain.interfaces.providers import LLMProvider, SpeechProvider
from voice_orchestrator.domain.models.core import GoldenSample
from voice_orchestrator.evaluation.metrics import (
    RegressionResult,
    compute_extraction_metrics,
    compute_transcription_metrics,
)

logger = structlog.get_logger(__name__)


@dataclass
class RegressionReport:
    total_samples: int = 0
    passed: int = 0
    failed: int = 0
    avg_wer: float = 0.0
    avg_cer: float = 0.0
    avg_intent_accuracy: float = 0.0
    avg_entity_f1: float = 0.0
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    results: list[RegressionResult] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_samples if self.total_samples > 0 else 0.0


class RegressionRunner:
    def __init__(
        self,
        stt_provider: SpeechProvider,
        llm_provider: LLMProvider,
        system_prompt: str,
        wer_threshold: float = 0.3,
        intent_accuracy_threshold: float = 0.8,
    ):
        self._stt = stt_provider
        self._llm = llm_provider
        self._system_prompt = system_prompt
        self._wer_threshold = wer_threshold
        self._intent_accuracy_threshold = intent_accuracy_threshold

    async def run(self, samples: list[GoldenSample]) -> RegressionReport:
        report = RegressionReport(
            total_samples=len(samples),
            config={
                "stt_provider": self._stt.name,
                "llm_provider": self._llm.name,
                "wer_threshold": self._wer_threshold,
                "intent_accuracy_threshold": self._intent_accuracy_threshold,
            },
        )

        total_wer = 0.0
        total_cer = 0.0
        total_intent_acc = 0.0
        total_entity_f1 = 0.0

        for sample in samples:
            result = await self._run_sample(sample)
            report.results.append(result)

            if result.passed:
                report.passed += 1
            else:
                report.failed += 1

            total_wer += result.transcription_metrics.wer
            total_cer += result.transcription_metrics.cer
            total_intent_acc += result.extraction_metrics.intent_accuracy
            total_entity_f1 += result.extraction_metrics.entity_f1

        n = len(samples) or 1
        report.avg_wer = total_wer / n
        report.avg_cer = total_cer / n
        report.avg_intent_accuracy = total_intent_acc / n
        report.avg_entity_f1 = total_entity_f1 / n

        logger.info(
            "regression_complete",
            total=report.total_samples,
            passed=report.passed,
            failed=report.failed,
            avg_wer=report.avg_wer,
            avg_intent_accuracy=report.avg_intent_accuracy,
        )

        return report

    async def _run_sample(self, sample: GoldenSample) -> RegressionResult:
        result = RegressionResult(sample_id=sample.id)

        try:
            # Read audio file
            with open(sample.audio_path, "rb") as f:
                audio_data = f.read()

            ext = sample.audio_path.rsplit(".", 1)[-1] if "." in sample.audio_path else "wav"

            # STT
            transcription = await self._stt.transcribe(audio_data, ext)

            # Evaluate transcription
            result.transcription_metrics = compute_transcription_metrics(
                sample.expected_transcript, transcription.transcript
            )

            # LLM extraction
            user_prompt = (
                f'Extract actions from this voice command:\n\n"{transcription.transcript}"'
            )
            extraction = await self._llm.generate(
                prompt=user_prompt,
                system_prompt=self._system_prompt,
            )

            # Evaluate extraction
            result.extraction_metrics = compute_extraction_metrics(
                sample.expected_actions, extraction.actions
            )

            # Determine pass/fail
            result.passed = (
                result.transcription_metrics.wer <= self._wer_threshold
                and result.extraction_metrics.intent_accuracy >= self._intent_accuracy_threshold
            )

            result.details = {
                "transcript": transcription.transcript,
                "actions": [a.model_dump() for a in extraction.actions],
                "stt_latency_ms": transcription.latency_ms,
                "llm_latency_ms": extraction.latency_ms,
            }

        except Exception as e:
            result.passed = False
            result.details = {"error": str(e)}
            logger.error("regression_sample_failed", sample_id=sample.id, error=str(e))

        return result
