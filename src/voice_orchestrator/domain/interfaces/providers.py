"""Provider interfaces (ports) for the voice orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from voice_orchestrator.domain.models.core import ExtractionResult, TranscriptionResult


class SpeechProvider(ABC):
    """Abstract interface for speech-to-text providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs: Any,
    ) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes.
            audio_format: Audio format (wav, mp3, etc).
            language: Language code.

        Returns:
            TranscriptionResult with transcript, confidence, latency, cost.
        """


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ExtractionResult:
        """Generate a structured extraction from a prompt.

        Args:
            prompt: User prompt with transcript.
            system_prompt: System-level instructions.
            temperature: Sampling temperature.
            max_tokens: Max output tokens.

        Returns:
            ExtractionResult with actions, latency, token usage, cost.
        """


class AudioStorage(ABC):
    """Abstract interface for audio file storage."""

    @abstractmethod
    async def store(self, audio_data: bytes, filename: str) -> str:
        """Store audio and return storage path."""

    @abstractmethod
    async def retrieve(self, storage_path: str) -> bytes:
        """Retrieve audio bytes from storage path."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete audio from storage."""
