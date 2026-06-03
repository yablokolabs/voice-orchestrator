"""Audio service — handles upload, validation, and storage."""

from __future__ import annotations

from voice_orchestrator.config import Settings
from voice_orchestrator.domain.exceptions import AudioValidationError
from voice_orchestrator.domain.interfaces.providers import AudioStorage
from voice_orchestrator.domain.interfaces.repositories import AudioFileRepository
from voice_orchestrator.domain.models.core import AudioFile, AudioFormat


class AudioService:
    def __init__(
        self,
        storage: AudioStorage,
        repo: AudioFileRepository,
        settings: Settings,
    ):
        self._storage = storage
        self._repo = repo
        self._settings = settings

    async def upload(
        self,
        audio_data: bytes,
        filename: str,
    ) -> AudioFile:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self._settings.allowed_audio_formats:
            raise AudioValidationError(
                f"Unsupported format '{ext}'. Allowed: {self._settings.allowed_audio_formats}"
            )

        size_mb = len(audio_data) / (1024 * 1024)
        if size_mb > self._settings.max_audio_size_mb:
            raise AudioValidationError(
                f"File too large ({size_mb:.1f}MB). Max: {self._settings.max_audio_size_mb}MB"
            )

        storage_path = await self._storage.store(audio_data, filename)

        audio_file = AudioFile(
            filename=filename,
            format=AudioFormat(ext),
            size_bytes=len(audio_data),
            storage_path=storage_path,
        )

        return await self._repo.save(audio_file)

    async def get(self, audio_id: str) -> AudioFile | None:
        return await self._repo.get_by_id(audio_id)

    async def get_audio_data(self, audio_id: str) -> bytes:
        audio_file = await self._repo.get_by_id(audio_id)
        if not audio_file:
            raise AudioValidationError(f"Audio file not found: {audio_id}")
        return await self._storage.retrieve(audio_file.storage_path)
