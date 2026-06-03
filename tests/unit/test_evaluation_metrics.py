"""Tests for evaluation metrics (WER, CER, extraction metrics)."""


from voice_orchestrator.domain.models.core import Action, IntentType
from voice_orchestrator.evaluation.metrics import (
    compute_cer,
    compute_extraction_metrics,
    compute_wer,
)


class TestComputeWER:
    def test_perfect_match_returns_zero(self):
        assert compute_wer("the cat sat", "the cat sat") == 0.0

    def test_complete_mismatch(self):
        wer = compute_wer("the cat sat", "a dog ran")
        assert wer > 0.0
        assert wer == 1.0  # 3/3 words wrong

    def test_empty_reference_nonempty_hypothesis_returns_one(self):
        assert compute_wer("", "some words") == 1.0

    def test_both_empty_returns_zero(self):
        assert compute_wer("", "") == 0.0

    def test_known_example(self):
        wer = compute_wer("the cat sat", "the bat sat")
        assert abs(wer - 1.0 / 3.0) < 0.01

    def test_case_insensitive(self):
        assert compute_wer("Hello World", "hello world") == 0.0


class TestComputeCER:
    def test_perfect_match_returns_zero(self):
        assert compute_cer("hello", "hello") == 0.0

    def test_known_example(self):
        cer = compute_cer("hello", "hallo")
        assert abs(cer - 0.2) < 0.01

    def test_empty_reference_nonempty_hypothesis(self):
        assert compute_cer("", "abc") == 1.0

    def test_both_empty(self):
        assert compute_cer("", "") == 0.0


class TestComputeExtractionMetrics:
    def test_matching_intents_and_entities(self):
        expected = [Action(intent=IntentType.CREATE_MEETING, person="Alice", date="2025-01-01")]
        predicted = [Action(intent=IntentType.CREATE_MEETING, person="Alice", date="2025-01-01")]
        metrics = compute_extraction_metrics(expected, predicted)
        assert metrics.intent_accuracy == 1.0
        assert metrics.entity_precision == 1.0
        assert metrics.entity_recall == 1.0

    def test_mismatched_intents(self):
        expected = [Action(intent=IntentType.CREATE_MEETING)]
        predicted = [Action(intent=IntentType.SEND_MESSAGE)]
        metrics = compute_extraction_metrics(expected, predicted)
        assert metrics.intent_accuracy == 0.0

    def test_partial_entity_matches(self):
        expected = [Action(intent=IntentType.CREATE_MEETING, person="Alice", date="2025-01-01")]
        predicted = [Action(intent=IntentType.CREATE_MEETING, person="Alice", date="2025-02-02")]
        metrics = compute_extraction_metrics(expected, predicted)
        # person matches, date doesn't => 1 correct out of 2 expected entities
        assert metrics.entity_recall == 0.5
        assert metrics.entity_precision == 0.5
        # F1 = 2 * 0.5 * 0.5 / (0.5 + 0.5) = 0.5
        assert abs(metrics.entity_f1 - 0.5) < 0.01

    def test_empty_expected_with_predictions(self):
        predicted = [Action(intent=IntentType.CREATE_MEETING, person="Bob")]
        metrics = compute_extraction_metrics([], predicted)
        assert metrics.intent_accuracy == 0.0

    def test_both_empty(self):
        metrics = compute_extraction_metrics([], [])
        assert metrics.intent_accuracy == 1.0
