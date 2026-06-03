"""Domain models for the voice orchestrator pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AudioFormat(StrEnum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    OGG = "ogg"
    FLAC = "flac"
    WEBM = "webm"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class IntentType(StrEnum):
    CREATE_MEETING = "create_meeting"
    CREATE_REMINDER = "create_reminder"
    SEND_MESSAGE = "send_message"
    CREATE_TASK = "create_task"
    SET_ALARM = "set_alarm"
    MAKE_CALL = "make_call"
    SEARCH = "search"
    UNKNOWN = "unknown"


class FeedbackStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"


# --- Core Domain Models ---


class AudioFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    format: AudioFormat
    size_bytes: int
    duration_seconds: float | None = None
    storage_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TranscriptionResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_file_id: str
    transcript: str
    confidence: float
    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    word_count: int = 0
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    intent: IntentType
    person: str | None = None
    date: str | None = None
    time: str | None = None
    message: str | None = None
    subject: str | None = None
    location: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transcription_id: str
    actions: list[Action]
    raw_text: str
    provider: str
    model: str
    prompt_id: str
    prompt_version: int
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_file_id: str
    transcription: TranscriptionResult
    extraction: ExtractionResult
    status: ProcessingStatus
    total_latency_ms: float
    total_cost_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PromptVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_id: str
    version: int
    template: str
    author: str
    change_reason: str
    is_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    extraction_id: str
    status: FeedbackStatus = FeedbackStatus.PENDING
    corrected_actions: list[Action] | None = None
    reviewer: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GoldenSample(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_path: str
    expected_transcript: str
    expected_actions: list[Action]
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderMetrics(BaseModel):
    provider: str
    model: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    avg_cost_usd: float = 0.0
    error_rate: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
