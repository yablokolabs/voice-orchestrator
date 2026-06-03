"""OpenAI Whisper speech-to-text provider."""

from __future__ import annotations

import io
import time
from typing import TYPE_CHECKING

import openai

from voice_orchestrator.domain.exceptions import TranscriptionError
from voice_orchestrator.domain.interfaces.providers import SpeechProvider
from voice_orchestrator.domain.models.core import TranscriptionResult

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

# Whisper API pricing: $0.006 per minute of audio
_COST_PER_MINUTE = 0.006


class WhisperProvider(SpeechProvider):
    """Speech-to-text provider using OpenAI Whisper API."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.whisper_model
        self._client = openai.AsyncOpenAI(api_key=settings.whisper_api_key)

    @property
    def name(self) -> str:
        return "whisper"

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs,
    ) -> TranscriptionResult:
        filename = f"audio.{audio_format}"
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        start = time.perf_counter()
        try:
            response = await self._client.audio.transcriptions.create(
                model=self._model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
            )
        except openai.OpenAIError as exc:
            raise TranscriptionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw = response.model_dump() if hasattr(response, "model_dump") else {}
        duration_seconds = getattr(response, "duration", 0.0) or 0.0
        transcript = response.text or ""
        cost = (duration_seconds / 60.0) * _COST_PER_MINUTE

        return TranscriptionResult(
            audio_file_id="",
            transcript=transcript,
            confidence=1.0,  # Whisper API doesn't return a confidence score
            provider=self.name,
            model=self._model,
            latency_ms=elapsed_ms,
            cost_usd=cost,
            word_count=len(transcript.split()) if transcript else 0,
            language=language,
            raw_response=raw,
        )
