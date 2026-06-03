"""SQL implementation of AudioFileRepository."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import AudioFileRepository
from voice_orchestrator.domain.models.core import AudioFile, AudioFormat
from voice_orchestrator.infrastructure.database.models.tables import AudioFileRow


class SqlAudioFileRepository(AudioFileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, audio_file: AudioFile) -> AudioFile:
        row = AudioFileRow(
            id=uuid.UUID(audio_file.id),
            filename=audio_file.filename,
            format=audio_file.format.value,
            size_bytes=audio_file.size_bytes,
            duration_seconds=audio_file.duration_seconds,
            storage_path=audio_file.storage_path,
            uploaded_at=audio_file.uploaded_at,
            metadata_=audio_file.metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return audio_file

    async def get_by_id(self, audio_id: str) -> AudioFile | None:
        row = await self._session.get(AudioFileRow, uuid.UUID(audio_id))
        if row is None:
            return None
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: AudioFileRow) -> AudioFile:
        return AudioFile(
            id=str(row.id),
            filename=row.filename,
            format=AudioFormat(row.format),
            size_bytes=row.size_bytes,
            duration_seconds=row.duration_seconds,
            storage_path=row.storage_path,
            uploaded_at=row.uploaded_at,
            metadata=row.metadata_,
        )
