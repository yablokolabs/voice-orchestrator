"""SQL implementation of GoldenSampleRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import GoldenSampleRepository
from voice_orchestrator.domain.models.core import Action, GoldenSample
from voice_orchestrator.infrastructure.database.models.tables import GoldenSampleRow


class SqlGoldenSampleRepository(GoldenSampleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, sample: GoldenSample) -> GoldenSample:
        row = GoldenSampleRow(
            id=uuid.UUID(sample.id),
            audio_path=sample.audio_path,
            expected_transcript=sample.expected_transcript,
            expected_actions=[a.model_dump() for a in sample.expected_actions],
            tags=sample.tags,
            created_at=sample.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return sample

    async def list_all(self) -> list[GoldenSample]:
        stmt = select(GoldenSampleRow).order_by(GoldenSampleRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_tags(self, tags: list[str]) -> list[GoldenSample]:
        stmt = select(GoldenSampleRow).where(
            GoldenSampleRow.tags.contains(tags)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    @staticmethod
    def _to_domain(row: GoldenSampleRow) -> GoldenSample:
        return GoldenSample(
            id=str(row.id),
            audio_path=row.audio_path,
            expected_transcript=row.expected_transcript,
            expected_actions=[Action(**a) for a in row.expected_actions],
            tags=row.tags if isinstance(row.tags, list) else [],
            created_at=row.created_at,
        )
