"""Transcription service — orchestrates STT with reliability."""

from __future__ import annotations

import structlog

from voice_orchestrator.domain.interfaces.providers import SpeechProvider
from voice_orchestrator.domain.interfaces.repositories import TranscriptionRepository
from voice_orchestrator.domain.models.core import TranscriptionResult
from voice_orchestrator.services.normalization import NormalizationService

logger = structlog.get_logger(__name__)


class TranscriptionService:
    def __init__(
        self,
        provider: SpeechProvider,
        repo: TranscriptionRepository,
        normalizer: NormalizationService,
    ):
        self._provider = provider
        self._repo = repo
        self._normalizer = normalizer

    async def transcribe(
        self,
        audio_data: bytes,
        audio_file_id: str,
        audio_format: str = "wav",
        language: str = "en",
    ) -> TranscriptionResult:
        logger.info(
            "transcribing_audio",
            provider=self._provider.name,
            audio_file_id=audio_file_id,
            format=audio_format,
        )

        result = await self._provider.transcribe(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language,
        )

        result.audio_file_id = audio_file_id
        result.transcript = self._normalizer.normalize(result.transcript)
        result.word_count = len(result.transcript.split())

        saved = await self._repo.save(result)

        logger.info(
            "transcription_complete",
            provider=self._provider.name,
            transcription_id=saved.id,
            word_count=saved.word_count,
            confidence=saved.confidence,
            latency_ms=saved.latency_ms,
        )

        return saved
