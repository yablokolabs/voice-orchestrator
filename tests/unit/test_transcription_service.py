"""Tests for TranscriptionService."""

import pytest

from tests.conftest import FakeSpeechProvider, InMemoryTranscriptionRepository
from voice_orchestrator.services.normalization import NormalizationService
from voice_orchestrator.services.transcription import TranscriptionService


@pytest.fixture
def transcription_service() -> TranscriptionService:
    provider = FakeSpeechProvider(transcript="um hello uh world")
    repo = InMemoryTranscriptionRepository()
    normalizer = NormalizationService()
    return TranscriptionService(provider=provider, repo=repo, normalizer=normalizer)


class TestTranscribe:
    async def test_returns_normalized_text(self, transcription_service: TranscriptionService):
        result = await transcription_service.transcribe(
            audio_data=b"fake audio",
            audio_file_id="audio-123",
        )
        # Fillers "um" and "uh" should be removed
        transcript_lower = result.transcript.lower()
        assert "um" not in transcript_lower.split()
        assert "uh" not in transcript_lower.split()
        assert "hello" in transcript_lower
        assert "world" in transcript_lower

    async def test_sets_correct_audio_file_id(self, transcription_service: TranscriptionService):
        result = await transcription_service.transcribe(
            audio_data=b"fake audio",
            audio_file_id="audio-456",
        )
        assert result.audio_file_id == "audio-456"

    async def test_sets_word_count(self, transcription_service: TranscriptionService):
        result = await transcription_service.transcribe(
            audio_data=b"fake audio",
            audio_file_id="audio-789",
        )
        assert result.word_count == len(result.transcript.split())

    async def test_saves_to_repository(self):
        provider = FakeSpeechProvider(transcript="simple test")
        repo = InMemoryTranscriptionRepository()
        normalizer = NormalizationService()
        service = TranscriptionService(provider=provider, repo=repo, normalizer=normalizer)

        result = await service.transcribe(audio_data=b"data", audio_file_id="a-1")
        stored = await repo.get_by_id(result.id)
        assert stored is not None
        assert stored.id == result.id
