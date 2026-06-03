"""SQL implementation of FeedbackRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import FeedbackRepository
from voice_orchestrator.domain.models.core import Action, Feedback, FeedbackStatus
from voice_orchestrator.infrastructure.database.models.tables import FeedbackRow


class SqlFeedbackRepository(FeedbackRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, feedback: Feedback) -> Feedback:
        corrected = (
            [a.model_dump() for a in feedback.corrected_actions]
            if feedback.corrected_actions is not None
            else None
        )
        row = FeedbackRow(
            id=uuid.UUID(feedback.id),
            extraction_id=uuid.UUID(feedback.extraction_id),
            status=feedback.status.value,
            corrected_actions=corrected,
            reviewer=feedback.reviewer,
            notes=feedback.notes,
            created_at=feedback.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return feedback

    async def get_by_id(self, feedback_id: str) -> Feedback | None:
        row = await self._session.get(FeedbackRow, uuid.UUID(feedback_id))
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_status(
        self, status: FeedbackStatus, limit: int = 50
    ) -> list[Feedback]:
        stmt = (
            select(FeedbackRow)
            .where(FeedbackRow.status == status.value)
            .order_by(FeedbackRow.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_extraction_id(self, extraction_id: str) -> Feedback | None:
        stmt = select(FeedbackRow).where(
            FeedbackRow.extraction_id == uuid.UUID(extraction_id)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: FeedbackRow) -> Feedback:
        corrected = (
            [Action(**a) for a in row.corrected_actions]
            if row.corrected_actions is not None
            else None
        )
        return Feedback(
            id=str(row.id),
            extraction_id=str(row.extraction_id),
            status=FeedbackStatus(row.status),
            corrected_actions=corrected,
            reviewer=row.reviewer,
            notes=row.notes,
            created_at=row.created_at,
        )
