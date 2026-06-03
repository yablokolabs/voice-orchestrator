"""SQL implementation of TranscriptionRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import TranscriptionRepository
from voice_orchestrator.domain.models.core import TranscriptionResult
from voice_orchestrator.infrastructure.database.models.tables import TranscriptionRow


class SqlTranscriptionRepository(TranscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: TranscriptionResult) -> TranscriptionResult:
        row = TranscriptionRow(
            id=uuid.UUID(result.id),
            audio_file_id=uuid.UUID(result.audio_file_id),
            transcript=result.transcript,
            confidence=result.confidence,
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            word_count=result.word_count,
            language=result.language,
            created_at=result.created_at,
            raw_response=result.raw_response,
        )
        self._session.add(row)
        await self._session.flush()
        return result

    async def get_by_id(self, transcription_id: str) -> TranscriptionResult | None:
        row = await self._session.get(TranscriptionRow, uuid.UUID(transcription_id))
        if row is None:
            return None
        return self._to_domain(row)

    async def get_by_audio_id(self, audio_id: str) -> list[TranscriptionResult]:
        stmt = select(TranscriptionRow).where(
            TranscriptionRow.audio_file_id == uuid.UUID(audio_id)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    @staticmethod
    def _to_domain(row: TranscriptionRow) -> TranscriptionResult:
        return TranscriptionResult(
            id=str(row.id),
            audio_file_id=str(row.audio_file_id),
            transcript=row.transcript,
            confidence=row.confidence,
            provider=row.provider,
            model=row.model,
            latency_ms=row.latency_ms,
            cost_usd=row.cost_usd,
            word_count=row.word_count,
            language=row.language,
            created_at=row.created_at,
            raw_response=row.raw_response,
        )
