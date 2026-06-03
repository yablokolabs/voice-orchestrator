"""SQL implementation of PromptRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from voice_orchestrator.domain.interfaces.repositories import PromptRepository
from voice_orchestrator.domain.models.core import PromptVersion
from voice_orchestrator.infrastructure.database.models.tables import PromptVersionRow


class SqlPromptRepository(PromptRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_version(self, version: PromptVersion) -> PromptVersion:
        row = PromptVersionRow(
            id=uuid.UUID(version.id),
            prompt_id=version.prompt_id,
            version=version.version,
            template=version.template,
            author=version.author,
            change_reason=version.change_reason,
            is_active=version.is_active,
            created_at=version.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return version

    async def get_active(self, prompt_id: str) -> PromptVersion | None:
        stmt = select(PromptVersionRow).where(
            PromptVersionRow.prompt_id == prompt_id,
            PromptVersionRow.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def get_version(self, prompt_id: str, version: int) -> PromptVersion | None:
        stmt = select(PromptVersionRow).where(
            PromptVersionRow.prompt_id == prompt_id,
            PromptVersionRow.version == version,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        stmt = (
            select(PromptVersionRow)
            .where(PromptVersionRow.prompt_id == prompt_id)
            .order_by(PromptVersionRow.version)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_prompts(self) -> list[str]:
        stmt = select(PromptVersionRow.prompt_id).distinct()
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def activate(self, prompt_id: str, version: int) -> PromptVersion:
        # Deactivate all other versions of the same prompt_id
        await self._session.execute(
            update(PromptVersionRow)
            .where(PromptVersionRow.prompt_id == prompt_id)
            .values(is_active=False)
        )
        # Activate the target version
        await self._session.execute(
            update(PromptVersionRow)
            .where(
                PromptVersionRow.prompt_id == prompt_id,
                PromptVersionRow.version == version,
            )
            .values(is_active=True)
        )
        await self._session.flush()

        activated = await self.get_version(prompt_id, version)
        if activated is None:
            raise ValueError(f"Prompt version {prompt_id}@{version} not found")
        return activated

    @staticmethod
    def _to_domain(row: PromptVersionRow) -> PromptVersion:
        return PromptVersion(
            id=str(row.id),
            prompt_id=row.prompt_id,
            version=row.version,
            template=row.template,
            author=row.author,
            change_reason=row.change_reason,
            is_active=row.is_active,
            created_at=row.created_at,
        )
