"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from voice_orchestrator.domain.models.core import (
    Action,
    FeedbackStatus,
    IntentType,
    ProcessingStatus,
)

# --- Request Schemas ---


class TranscribeRequest(BaseModel):
    audio_file_id: str
    provider: str | None = None
    language: str = "en"


class ExtractActionsRequest(BaseModel):
    text: str | None = None
    audio_file_id: str | None = None
    provider: str | None = None
    prompt_id: str = "default"


class EvaluateRequest(BaseModel):
    extraction_id: str
    expected_actions: list[Action]


class ActivatePromptRequest(BaseModel):
    prompt_id: str
    version: int


class CreatePromptRequest(BaseModel):
    prompt_id: str
    template: str
    author: str
    change_reason: str
    activate: bool = False


class FeedbackRequest(BaseModel):
    extraction_id: str
    status: FeedbackStatus
    corrected_actions: list[Action] | None = None
    reviewer: str | None = None
    notes: str | None = None


class ProviderCompareRequest(BaseModel):
    text: str
    stt_providers: list[str] = Field(default_factory=list)
    llm_providers: list[str] = Field(default_factory=list)
    prompt_id: str = "default"


# --- Response Schemas ---


class AudioUploadResponse(BaseModel):
    audio_file_id: str
    filename: str
    format: str
    size_bytes: int
    uploaded_at: datetime


class TranscriptionResponse(BaseModel):
    id: str
    audio_file_id: str
    transcript: str
    confidence: float
    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    word_count: int


class ActionResponse(BaseModel):
    intent: IntentType
    person: str | None = None
    date: str | None = None
    time: str | None = None
    message: str | None = None
    subject: str | None = None
    location: str | None = None


class ExtractionResponse(BaseModel):
    id: str
    transcription_id: str
    actions: list[ActionResponse]
    provider: str
    model: str
    prompt_id: str
    prompt_version: int
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float


class PipelineResponse(BaseModel):
    id: str
    audio_file_id: str
    transcription: TranscriptionResponse
    extraction: ExtractionResponse
    status: ProcessingStatus
    total_latency_ms: float
    total_cost_usd: float


class EvaluationResponse(BaseModel):
    extraction_id: str
    intent_accuracy: float
    entity_precision: float
    entity_recall: float
    entity_f1: float


class PromptVersionResponse(BaseModel):
    id: str
    prompt_id: str
    version: int
    template: str
    author: str
    change_reason: str
    is_active: bool
    created_at: datetime


class FeedbackResponse(BaseModel):
    id: str
    extraction_id: str
    status: FeedbackStatus
    reviewer: str | None
    notes: str | None
    created_at: datetime


class MetricsResponse(BaseModel):
    total_requests: int = 0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    by_provider: dict = Field(default_factory=dict)


class ProviderCompareResponse(BaseModel):
    results: list[dict]


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    environment: str
