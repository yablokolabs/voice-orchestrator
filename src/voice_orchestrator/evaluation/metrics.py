"""Evaluation metrics — WER, CER, intent accuracy, entity accuracy."""

from __future__ import annotations

from dataclasses import dataclass, field

from voice_orchestrator.domain.models.core import Action


@dataclass
class TranscriptionMetrics:
    wer: float = 0.0
    cer: float = 0.0
    word_count_ref: int = 0
    word_count_hyp: int = 0


@dataclass
class ExtractionMetrics:
    intent_accuracy: float = 0.0
    entity_precision: float = 0.0
    entity_recall: float = 0.0
    entity_f1: float = 0.0
    total_expected: int = 0
    total_predicted: int = 0
    correct_intents: int = 0
    correct_entities: int = 0


@dataclass
class ProductionMetrics:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    retries: int = 0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    retry_rate: float = 0.0
    hallucination_rate: float = 0.0


@dataclass
class CostMetrics:
    total_cost_usd: float = 0.0
    avg_cost_per_request: float = 0.0
    cost_by_provider: dict[str, float] = field(default_factory=dict)


@dataclass
class RegressionResult:
    sample_id: str = ""
    passed: bool = True
    transcription_metrics: TranscriptionMetrics = field(default_factory=TranscriptionMetrics)
    extraction_metrics: ExtractionMetrics = field(default_factory=ExtractionMetrics)
    details: dict = field(default_factory=dict)


def compute_wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate using dynamic programming."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def compute_cer(reference: str, hypothesis: str) -> float:
    """Compute Character Error Rate using dynamic programming."""
    ref_chars = list(reference.lower())
    hyp_chars = list(hypothesis.lower())

    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    d = [[0] * (len(hyp_chars) + 1) for _ in range(len(ref_chars) + 1)]

    for i in range(len(ref_chars) + 1):
        d[i][0] = i
    for j in range(len(hyp_chars) + 1):
        d[0][j] = j

    for i in range(1, len(ref_chars) + 1):
        for j in range(1, len(hyp_chars) + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])

    return d[len(ref_chars)][len(hyp_chars)] / len(ref_chars)


def compute_transcription_metrics(reference: str, hypothesis: str) -> TranscriptionMetrics:
    return TranscriptionMetrics(
        wer=compute_wer(reference, hypothesis),
        cer=compute_cer(reference, hypothesis),
        word_count_ref=len(reference.split()),
        word_count_hyp=len(hypothesis.split()),
    )


def compute_extraction_metrics(
    expected: list[Action],
    predicted: list[Action],
) -> ExtractionMetrics:
    """Compute intent and entity accuracy between expected and predicted actions."""
    if not expected:
        return ExtractionMetrics(
            intent_accuracy=1.0 if not predicted else 0.0,
            total_expected=0,
            total_predicted=len(predicted),
        )

    correct_intents = 0
    total_correct_entities = 0
    total_expected_entities = 0
    total_predicted_entities = 0

    for i, exp in enumerate(expected):
        if i < len(predicted):
            pred = predicted[i]
            if exp.intent == pred.intent:
                correct_intents += 1

            entity_fields = ["person", "date", "time", "message", "subject", "location"]
            for field_name in entity_fields:
                exp_val = getattr(exp, field_name)
                pred_val = getattr(pred, field_name)

                if exp_val is not None:
                    total_expected_entities += 1
                    if pred_val is not None and str(exp_val).lower() == str(pred_val).lower():
                        total_correct_entities += 1

                if pred_val is not None:
                    total_predicted_entities += 1

    intent_accuracy = correct_intents / len(expected) if expected else 0.0

    precision = (
        total_correct_entities / total_predicted_entities
        if total_predicted_entities > 0
        else 0.0
    )
    recall = (
        total_correct_entities / total_expected_entities
        if total_expected_entities > 0
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return ExtractionMetrics(
        intent_accuracy=intent_accuracy,
        entity_precision=precision,
        entity_recall=recall,
        entity_f1=f1,
        total_expected=len(expected),
        total_predicted=len(predicted),
        correct_intents=correct_intents,
        correct_entities=total_correct_entities,
    )
