"""SQL implementation of PipelineResultRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from voice_orchestrator.domain.interfaces.repositories import PipelineResultRepository
from voice_orchestrator.domain.models.core import (
    Action,
    ExtractionResult,
    PipelineResult,
    ProcessingStatus,
    TranscriptionResult,
)
from voice_orchestrator.infrastructure.database.models.tables import (
    ExtractionRow,
    PipelineResultRow,
    TranscriptionRow,
)


class SqlPipelineResultRepository(PipelineResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: PipelineResult) -> PipelineResult:
        row = PipelineResultRow(
            id=uuid.UUID(result.id),
            audio_file_id=uuid.UUID(result.audio_file_id),
            transcription_id=uuid.UUID(result.transcription.id),
            extraction_id=uuid.UUID(result.extraction.id),
            status=result.status.value,
            total_latency_ms=result.total_latency_ms,
            total_cost_usd=result.total_cost_usd,
            created_at=result.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return result

    async def get_by_id(self, result_id: str) -> PipelineResult | None:
        stmt = (
            select(PipelineResultRow)
            .options(
                selectinload(PipelineResultRow.transcription),
                selectinload(PipelineResultRow.extraction),
            )
            .where(PipelineResultRow.id == uuid.UUID(result_id))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_recent(self, limit: int = 50) -> list[PipelineResult]:
        stmt = (
            select(PipelineResultRow)
            .options(
                selectinload(PipelineResultRow.transcription),
                selectinload(PipelineResultRow.extraction),
            )
            .order_by(PipelineResultRow.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    @staticmethod
    def _transcription_to_domain(row: TranscriptionRow) -> TranscriptionResult:
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

    @staticmethod
    def _extraction_to_domain(row: ExtractionRow) -> ExtractionResult:
        return ExtractionResult(
            id=str(row.id),
            transcription_id=str(row.transcription_id),
            actions=[Action(**a) for a in row.actions],
            raw_text=row.raw_text,
            provider=row.provider,
            model=row.model,
            prompt_id=row.prompt_id,
            prompt_version=row.prompt_version,
            latency_ms=row.latency_ms,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            cost_usd=row.cost_usd,
            created_at=row.created_at,
            raw_response=row.raw_response,
        )

    @classmethod
    def _to_domain(cls, row: PipelineResultRow) -> PipelineResult:
        return PipelineResult(
            id=str(row.id),
            audio_file_id=str(row.audio_file_id),
            transcription=cls._transcription_to_domain(row.transcription),
            extraction=cls._extraction_to_domain(row.extraction),
            status=ProcessingStatus(row.status),
            total_latency_ms=row.total_latency_ms,
            total_cost_usd=row.total_cost_usd,
            created_at=row.created_at,
        )
