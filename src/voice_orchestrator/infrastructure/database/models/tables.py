"""SQLAlchemy ORM models for the voice orchestrator database."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AudioFileRow(Base):
    __tablename__ = "audio_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, server_default="{}", nullable=False
    )

    transcriptions: Mapped[list[TranscriptionRow]] = relationship(back_populates="audio_file")
    pipeline_results: Mapped[list[PipelineResultRow]] = relationship(back_populates="audio_file")


class TranscriptionRow(Base):
    __tablename__ = "transcriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id"), nullable=False
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    audio_file: Mapped[AudioFileRow] = relationship(back_populates="transcriptions")
    extractions: Mapped[list[ExtractionRow]] = relationship(back_populates="transcription")
    pipeline_results: Mapped[list[PipelineResultRow]] = relationship(
        back_populates="transcription"
    )


class ExtractionRow(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcriptions.id"), nullable=False
    )
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    transcription: Mapped[TranscriptionRow] = relationship(back_populates="extractions")
    pipeline_results: Mapped[list[PipelineResultRow]] = relationship(back_populates="extraction")
    feedback: Mapped[list[FeedbackRow]] = relationship(back_populates="extraction")


class PipelineResultRow(Base):
    __tablename__ = "pipeline_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id"), nullable=False
    )
    transcription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcriptions.id"), nullable=False
    )
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    audio_file: Mapped[AudioFileRow] = relationship(back_populates="pipeline_results")
    transcription: Mapped[TranscriptionRow] = relationship(back_populates="pipeline_results")
    extraction: Mapped[ExtractionRow] = relationship(back_populates="pipeline_results")


class PromptVersionRow(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("prompt_id", "version", name="uq_prompt_id_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class FeedbackRow(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    corrected_actions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    extraction: Mapped[ExtractionRow] = relationship(back_populates="feedback")


class GoldenSampleRow(Base):
    __tablename__ = "golden_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    expected_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    expected_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class ProviderMetricsRow(Base):
    __tablename__ = "provider_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    request_type: Mapped[str] = mapped_column(String(10), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
