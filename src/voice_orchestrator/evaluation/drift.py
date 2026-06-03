"""Drift detection — monitors changes in prompt behavior, output schema, and distributions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from voice_orchestrator.domain.models.core import ExtractionResult


@dataclass
class DriftReport:
    prompt_drift: float = 0.0
    output_drift: float = 0.0
    schema_drift: float = 0.0
    intent_distribution_current: dict[str, float] = field(default_factory=dict)
    intent_distribution_baseline: dict[str, float] = field(default_factory=dict)
    missing_fields_rate: float = 0.0
    new_fields_rate: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class DriftDetector:
    """Detects drift in LLM outputs compared to a baseline."""

    def compute_intent_distribution(self, results: list[ExtractionResult]) -> dict[str, float]:
        counter: Counter[str] = Counter()
        total = 0
        for r in results:
            for action in r.actions:
                counter[action.intent] += 1
                total += 1

        if total == 0:
            return {}

        return {intent: count / total for intent, count in counter.items()}

    def compute_output_drift(
        self,
        baseline: list[ExtractionResult],
        current: list[ExtractionResult],
    ) -> float:
        """Jensen-Shannon-like divergence between intent distributions."""
        dist_a = self.compute_intent_distribution(baseline)
        dist_b = self.compute_intent_distribution(current)

        all_intents = set(dist_a.keys()) | set(dist_b.keys())
        if not all_intents:
            return 0.0

        divergence = 0.0
        for intent in all_intents:
            p = dist_a.get(intent, 0.0)
            q = dist_b.get(intent, 0.0)
            divergence += abs(p - q)

        return divergence / 2.0

    def compute_schema_drift(
        self,
        baseline: list[ExtractionResult],
        current: list[ExtractionResult],
    ) -> float:
        """Measure how often current outputs have different field patterns than baseline."""
        baseline_patterns = self._extract_field_patterns(baseline)
        current_patterns = self._extract_field_patterns(current)

        if not baseline_patterns:
            return 0.0

        novel = current_patterns - baseline_patterns
        return len(novel) / len(current_patterns) if current_patterns else 0.0

    def detect(
        self,
        baseline: list[ExtractionResult],
        current: list[ExtractionResult],
    ) -> DriftReport:
        output_drift = self.compute_output_drift(baseline, current)
        schema_drift = self.compute_schema_drift(baseline, current)

        return DriftReport(
            output_drift=output_drift,
            schema_drift=schema_drift,
            intent_distribution_baseline=self.compute_intent_distribution(baseline),
            intent_distribution_current=self.compute_intent_distribution(current),
        )

    def _extract_field_patterns(self, results: list[ExtractionResult]) -> set[frozenset[str]]:
        patterns: set[frozenset[str]] = set()
        for r in results:
            for action in r.actions:
                fields = set()
                for f in ["person", "date", "time", "message", "subject", "location"]:
                    if getattr(action, f) is not None:
                        fields.add(f)
                patterns.add(frozenset(fields))
        return patterns
