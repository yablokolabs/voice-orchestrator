"""Tests for DriftDetector."""

import pytest

from voice_orchestrator.domain.models.core import Action, ExtractionResult, IntentType
from voice_orchestrator.evaluation.drift import DriftDetector, DriftReport


def _make_extraction(actions: list[Action]) -> ExtractionResult:
    return ExtractionResult(
        transcription_id="t-1",
        actions=actions,
        raw_text="test",
        provider="fake",
        model="fake",
        prompt_id="default",
        prompt_version=1,
        latency_ms=10.0,
        input_tokens=10,
        output_tokens=10,
        cost_usd=0.001,
    )


@pytest.fixture
def detector() -> DriftDetector:
    return DriftDetector()


class TestComputeOutputDrift:
    def test_identical_distributions_returns_zero(self, detector: DriftDetector):
        data = [_make_extraction([Action(intent=IntentType.CREATE_MEETING)])]
        assert detector.compute_output_drift(data, data) == 0.0

    def test_different_distributions_returns_positive(self, detector: DriftDetector):
        baseline = [_make_extraction([Action(intent=IntentType.CREATE_MEETING)])]
        current = [_make_extraction([Action(intent=IntentType.SEND_MESSAGE)])]
        drift = detector.compute_output_drift(baseline, current)
        assert drift > 0.0

    def test_empty_lists_returns_zero(self, detector: DriftDetector):
        assert detector.compute_output_drift([], []) == 0.0


class TestComputeSchemaDrift:
    def test_same_patterns_returns_zero(self, detector: DriftDetector):
        data = [_make_extraction([Action(intent=IntentType.CREATE_MEETING, person="Alice")])]
        assert detector.compute_schema_drift(data, data) == 0.0

    def test_different_patterns_returns_positive(self, detector: DriftDetector):
        baseline = [_make_extraction([Action(intent=IntentType.CREATE_MEETING, person="Alice")])]
        current = [_make_extraction([Action(intent=IntentType.CREATE_MEETING, date="2025-01-01")])]
        drift = detector.compute_schema_drift(baseline, current)
        assert drift > 0.0


class TestDetect:
    def test_returns_drift_report_with_all_fields(self, detector: DriftDetector):
        baseline = [_make_extraction([Action(intent=IntentType.CREATE_MEETING)])]
        current = [_make_extraction([Action(intent=IntentType.SEND_MESSAGE)])]
        report = detector.detect(baseline, current)

        assert isinstance(report, DriftReport)
        assert isinstance(report.output_drift, float)
        assert isinstance(report.schema_drift, float)
        assert isinstance(report.intent_distribution_baseline, dict)
        assert isinstance(report.intent_distribution_current, dict)
