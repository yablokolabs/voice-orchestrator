"""SQL implementation of ExtractionRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import ExtractionRepository
from voice_orchestrator.domain.models.core import Action, ExtractionResult
from voice_orchestrator.infrastructure.database.models.tables import ExtractionRow


class SqlExtractionRepository(ExtractionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: ExtractionResult) -> ExtractionResult:
        row = ExtractionRow(
            id=uuid.UUID(result.id),
            transcription_id=uuid.UUID(result.transcription_id),
            actions=[a.model_dump() for a in result.actions],
            raw_text=result.raw_text,
            provider=result.provider,
            model=result.model,
            prompt_id=result.prompt_id,
            prompt_version=result.prompt_version,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            created_at=result.created_at,
            raw_response=result.raw_response,
        )
        self._session.add(row)
        await self._session.flush()
        return result

    async def get_by_id(self, extraction_id: str) -> ExtractionResult | None:
        row = await self._session.get(ExtractionRow, uuid.UUID(extraction_id))
        if row is None:
            return None
        return self._to_domain(row)

    async def get_by_transcription_id(
        self, transcription_id: str
    ) -> list[ExtractionResult]:
        stmt = select(ExtractionRow).where(
            ExtractionRow.transcription_id == uuid.UUID(transcription_id)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    @staticmethod
    def _to_domain(row: ExtractionRow) -> ExtractionResult:
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
