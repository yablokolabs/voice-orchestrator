"""Tests for AudioService — uses real LocalAudioStorage, in-memory repo."""

from pathlib import Path

import pytest

from tests.conftest import InMemoryAudioFileRepository
from voice_orchestrator.config import Settings
from voice_orchestrator.domain.exceptions import AudioValidationError
from voice_orchestrator.infrastructure.storage import LocalAudioStorage
from voice_orchestrator.services.audio import AudioService


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def audio_service(upload_dir: Path, settings: Settings) -> AudioService:
    settings.upload_dir = upload_dir
    storage = LocalAudioStorage(upload_dir)
    repo = InMemoryAudioFileRepository()
    return AudioService(storage=storage, repo=repo, settings=settings)


class TestUpload:
    async def test_rejects_unsupported_format(self, audio_service: AudioService):
        with pytest.raises(AudioValidationError, match="Unsupported format"):
            await audio_service.upload(b"fake audio data", "test.xyz")

    async def test_rejects_oversized_file(self, audio_service: AudioService, settings: Settings):
        # settings.max_audio_size_mb is 1, so > 1 MB should be rejected
        big_data = b"\x00" * (2 * 1024 * 1024)
        with pytest.raises(AudioValidationError, match="too large"):
            await audio_service.upload(big_data, "big.wav")

    async def test_stores_file_and_returns_audio_file(
        self, audio_service: AudioService, upload_dir: Path,
    ):
        data = b"RIFF" + b"\x00" * 100
        result = await audio_service.upload(data, "recording.wav")

        assert result.filename == "recording.wav"
        assert result.format == "wav"
        assert result.size_bytes == len(data)
        assert result.storage_path  # non-empty
        assert result.id  # non-empty UUID

    async def test_file_persisted_on_disk(self, audio_service: AudioService, upload_dir: Path):
        data = b"audio content"
        result = await audio_service.upload(data, "sample.mp3")
        stored = Path(result.storage_path)
        assert stored.exists()
        assert stored.read_bytes() == data
