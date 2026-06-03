"""Repository interfaces for the voice orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod

from voice_orchestrator.domain.models.core import (
    AudioFile,
    ExtractionResult,
    Feedback,
    FeedbackStatus,
    GoldenSample,
    PipelineResult,
    PromptVersion,
    TranscriptionResult,
)


class AudioFileRepository(ABC):
    @abstractmethod
    async def save(self, audio_file: AudioFile) -> AudioFile:
        ...

    @abstractmethod
    async def get_by_id(self, audio_id: str) -> AudioFile | None:
        ...


class TranscriptionRepository(ABC):
    @abstractmethod
    async def save(self, result: TranscriptionResult) -> TranscriptionResult:
        ...

    @abstractmethod
    async def get_by_id(self, transcription_id: str) -> TranscriptionResult | None:
        ...

    @abstractmethod
    async def get_by_audio_id(self, audio_id: str) -> list[TranscriptionResult]:
        ...


class ExtractionRepository(ABC):
    @abstractmethod
    async def save(self, result: ExtractionResult) -> ExtractionResult:
        ...

    @abstractmethod
    async def get_by_id(self, extraction_id: str) -> ExtractionResult | None:
        ...

    @abstractmethod
    async def get_by_transcription_id(self, transcription_id: str) -> list[ExtractionResult]:
        ...


class PipelineResultRepository(ABC):
    @abstractmethod
    async def save(self, result: PipelineResult) -> PipelineResult:
        ...

    @abstractmethod
    async def get_by_id(self, result_id: str) -> PipelineResult | None:
        ...

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> list[PipelineResult]:
        ...


class PromptRepository(ABC):
    @abstractmethod
    async def save_version(self, version: PromptVersion) -> PromptVersion:
        ...

    @abstractmethod
    async def get_active(self, prompt_id: str) -> PromptVersion | None:
        ...

    @abstractmethod
    async def get_version(self, prompt_id: str, version: int) -> PromptVersion | None:
        ...

    @abstractmethod
    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        ...

    @abstractmethod
    async def list_prompts(self) -> list[str]:
        ...

    @abstractmethod
    async def activate(self, prompt_id: str, version: int) -> PromptVersion:
        ...


class FeedbackRepository(ABC):
    @abstractmethod
    async def save(self, feedback: Feedback) -> Feedback:
        ...

    @abstractmethod
    async def get_by_id(self, feedback_id: str) -> Feedback | None:
        ...

    @abstractmethod
    async def list_by_status(
        self, status: FeedbackStatus, limit: int = 50
    ) -> list[Feedback]:
        ...

    @abstractmethod
    async def get_by_extraction_id(self, extraction_id: str) -> Feedback | None:
        ...


class GoldenSampleRepository(ABC):
    @abstractmethod
    async def save(self, sample: GoldenSample) -> GoldenSample:
        ...

    @abstractmethod
    async def list_all(self) -> list[GoldenSample]:
        ...

    @abstractmethod
    async def get_by_tags(self, tags: list[str]) -> list[GoldenSample]:
        ...
