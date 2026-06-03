"""Prometheus metrics for the voice orchestrator pipeline."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Request-level metrics
REQUESTS_TOTAL = Counter(
    "vo_requests_total",
    "Total pipeline requests",
    ["endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "vo_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# STT metrics
STT_REQUESTS = Counter(
    "vo_stt_requests_total",
    "Total STT provider requests",
    ["provider", "status"],
)

STT_LATENCY = Histogram(
    "vo_stt_latency_seconds",
    "STT provider latency",
    ["provider"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

STT_COST = Counter(
    "vo_stt_cost_usd_total",
    "Total STT cost in USD",
    ["provider"],
)

# LLM metrics
LLM_REQUESTS = Counter(
    "vo_llm_requests_total",
    "Total LLM provider requests",
    ["provider", "status"],
)

LLM_LATENCY = Histogram(
    "vo_llm_latency_seconds",
    "LLM provider latency",
    ["provider"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

LLM_TOKENS = Counter(
    "vo_llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "type"],
)

LLM_COST = Counter(
    "vo_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["provider"],
)

# Evaluation metrics
EVALUATION_INTENT_ACCURACY = Histogram(
    "vo_evaluation_intent_accuracy",
    "Intent accuracy distribution",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

EVALUATION_WER = Histogram(
    "vo_evaluation_wer",
    "Word Error Rate distribution",
    buckets=[0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0],
)

# Reliability metrics
CIRCUIT_BREAKER_STATE = Gauge(
    "vo_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["provider"],
)

RETRY_COUNT = Counter(
    "vo_retry_total",
    "Total retry attempts",
    ["provider", "operation"],
)

FALLBACK_COUNT = Counter(
    "vo_fallback_total",
    "Total fallback invocations",
    ["from_provider", "to_provider"],
)

DLQ_SIZE = Gauge(
    "vo_dlq_size",
    "Dead letter queue size",
)

# Pipeline metrics
PIPELINE_ACTIVE = Gauge(
    "vo_pipeline_active_requests",
    "Currently processing pipeline requests",
)

PIPELINE_COST_TOTAL = Counter(
    "vo_pipeline_cost_usd_total",
    "Total pipeline cost in USD",
)
