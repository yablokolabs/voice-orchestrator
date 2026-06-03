"""Prompt management service — versioning, activation, rollback."""

from __future__ import annotations

import structlog

from voice_orchestrator.domain.exceptions import PromptNotFoundError
from voice_orchestrator.domain.interfaces.repositories import PromptRepository
from voice_orchestrator.domain.models.core import PromptVersion

logger = structlog.get_logger(__name__)


class PromptService:
    def __init__(self, repo: PromptRepository):
        self._repo = repo

    async def create_version(
        self,
        prompt_id: str,
        template: str,
        author: str,
        change_reason: str,
        activate: bool = False,
    ) -> PromptVersion:
        existing = await self._repo.list_versions(prompt_id)
        next_version = max((v.version for v in existing), default=0) + 1

        version = PromptVersion(
            prompt_id=prompt_id,
            version=next_version,
            template=template,
            author=author,
            change_reason=change_reason,
            is_active=activate,
        )

        saved = await self._repo.save_version(version)

        if activate:
            await self._repo.activate(prompt_id, next_version)

        logger.info(
            "prompt_version_created",
            prompt_id=prompt_id,
            version=next_version,
            active=activate,
        )

        return saved

    async def activate(self, prompt_id: str, version: int) -> PromptVersion:
        v = await self._repo.get_version(prompt_id, version)
        if not v:
            raise PromptNotFoundError(f"Prompt {prompt_id} v{version} not found")

        activated = await self._repo.activate(prompt_id, version)

        logger.info("prompt_activated", prompt_id=prompt_id, version=version)
        return activated

    async def rollback(self, prompt_id: str) -> PromptVersion:
        versions = await self._repo.list_versions(prompt_id)
        active_versions = [v for v in versions if v.is_active]

        if not active_versions:
            raise PromptNotFoundError(f"No active version for prompt {prompt_id}")

        current = active_versions[0]
        previous = [v for v in versions if v.version < current.version]

        if not previous:
            raise PromptNotFoundError(f"No previous version to rollback to for {prompt_id}")

        target = max(previous, key=lambda v: v.version)
        return await self.activate(prompt_id, target.version)

    async def get_active(self, prompt_id: str) -> PromptVersion | None:
        return await self._repo.get_active(prompt_id)

    async def list_prompts(self) -> list[str]:
        return await self._repo.list_prompts()

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        return await self._repo.list_versions(prompt_id)
