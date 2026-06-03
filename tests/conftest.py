"""Shared fixtures and test doubles for the voice orchestrator test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from voice_orchestrator.config import Settings
from voice_orchestrator.domain.interfaces.providers import LLMProvider, SpeechProvider
from voice_orchestrator.domain.interfaces.repositories import (
    AudioFileRepository,
    ExtractionRepository,
    FeedbackRepository,
    PromptRepository,
    TranscriptionRepository,
)
from voice_orchestrator.domain.models.core import (
    Action,
    AudioFile,
    ExtractionResult,
    Feedback,
    FeedbackStatus,
    IntentType,
    PromptVersion,
    TranscriptionResult,
)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=tmp_path / "uploads",
        max_audio_size_mb=1,
        allowed_audio_formats=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        debug=True,
        environment="test",
        database_url="sqlite+aiosqlite:///test.db",
    )


# ---------------------------------------------------------------------------
# Provider test doubles
# ---------------------------------------------------------------------------


class FakeSpeechProvider(SpeechProvider):
    """Concrete test double that returns canned transcription results."""

    def __init__(self, transcript: str = "hello world", confidence: float = 0.95):
        self._transcript = transcript
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "fake-stt"

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs,
    ) -> TranscriptionResult:
        return TranscriptionResult(
            audio_file_id="",
            transcript=self._transcript,
            confidence=self._confidence,
            provider=self.name,
            model="fake-model",
            latency_ms=42.0,
            cost_usd=0.001,
        )


class FakeLLMProvider(LLMProvider):
    """Concrete test double that returns canned extraction results."""

    def __init__(self, actions: list[Action] | None = None):
        self._actions = actions or [
            Action(intent=IntentType.CREATE_MEETING, person="Alice", date="2025-01-01")
        ]

    @property
    def name(self) -> str:
        return "fake-llm"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> ExtractionResult:
        return ExtractionResult(
            transcription_id="",
            actions=self._actions,
            raw_text="",
            provider=self.name,
            model="fake-model",
            prompt_id="",
            prompt_version=0,
            latency_ms=100.0,
            input_tokens=50,
            output_tokens=30,
            cost_usd=0.002,
        )


# ---------------------------------------------------------------------------
# Repository test doubles
# ---------------------------------------------------------------------------


class InMemoryAudioFileRepository(AudioFileRepository):
    def __init__(self):
        self._store: dict[str, AudioFile] = {}

    async def save(self, audio_file: AudioFile) -> AudioFile:
        self._store[audio_file.id] = audio_file
        return audio_file

    async def get_by_id(self, audio_id: str) -> AudioFile | None:
        return self._store.get(audio_id)


class InMemoryTranscriptionRepository(TranscriptionRepository):
    def __init__(self):
        self._store: dict[str, TranscriptionResult] = {}

    async def save(self, result: TranscriptionResult) -> TranscriptionResult:
        self._store[result.id] = result
        return result

    async def get_by_id(self, transcription_id: str) -> TranscriptionResult | None:
        return self._store.get(transcription_id)

    async def get_by_audio_id(self, audio_id: str) -> list[TranscriptionResult]:
        return [r for r in self._store.values() if r.audio_file_id == audio_id]


class InMemoryExtractionRepository(ExtractionRepository):
    def __init__(self):
        self._store: dict[str, ExtractionResult] = {}

    async def save(self, result: ExtractionResult) -> ExtractionResult:
        self._store[result.id] = result
        return result

    async def get_by_id(self, extraction_id: str) -> ExtractionResult | None:
        return self._store.get(extraction_id)

    async def get_by_transcription_id(self, transcription_id: str) -> list[ExtractionResult]:
        return [r for r in self._store.values() if r.transcription_id == transcription_id]


class InMemoryPromptRepository(PromptRepository):
    def __init__(self):
        self._versions: list[PromptVersion] = []

    async def save_version(self, version: PromptVersion) -> PromptVersion:
        self._versions.append(version)
        return version

    async def get_active(self, prompt_id: str) -> PromptVersion | None:
        for v in reversed(self._versions):
            if v.prompt_id == prompt_id and v.is_active:
                return v
        return None

    async def get_version(self, prompt_id: str, version: int) -> PromptVersion | None:
        for v in self._versions:
            if v.prompt_id == prompt_id and v.version == version:
                return v
        return None

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        return [v for v in self._versions if v.prompt_id == prompt_id]

    async def list_prompts(self) -> list[str]:
        return list({v.prompt_id for v in self._versions})

    async def activate(self, prompt_id: str, version: int) -> PromptVersion:
        target = None
        for v in self._versions:
            if v.prompt_id == prompt_id:
                if v.version == version:
                    v.is_active = True
                    target = v
                else:
                    v.is_active = False
        assert target is not None
        return target


class InMemoryFeedbackRepository(FeedbackRepository):
    def __init__(self):
        self._store: dict[str, Feedback] = {}

    async def save(self, feedback: Feedback) -> Feedback:
        self._store[feedback.id] = feedback
        return feedback

    async def get_by_id(self, feedback_id: str) -> Feedback | None:
        return self._store.get(feedback_id)

    async def list_by_status(self, status: FeedbackStatus, limit: int = 50) -> list[Feedback]:
        return [f for f in self._store.values() if f.status == status][:limit]

    async def get_by_extraction_id(self, extraction_id: str) -> Feedback | None:
        for f in self._store.values():
            if f.extraction_id == extraction_id:
                return f
        return None


# ---------------------------------------------------------------------------
# Fixtures that provide ready-to-use test doubles
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_speech_provider() -> FakeSpeechProvider:
    return FakeSpeechProvider()


@pytest.fixture
def fake_llm_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def audio_file_repo() -> InMemoryAudioFileRepository:
    return InMemoryAudioFileRepository()


@pytest.fixture
def transcription_repo() -> InMemoryTranscriptionRepository:
    return InMemoryTranscriptionRepository()


@pytest.fixture
def extraction_repo() -> InMemoryExtractionRepository:
    return InMemoryExtractionRepository()


@pytest.fixture
def prompt_repo() -> InMemoryPromptRepository:
    return InMemoryPromptRepository()


@pytest.fixture
def feedback_repo() -> InMemoryFeedbackRepository:
    return InMemoryFeedbackRepository()
