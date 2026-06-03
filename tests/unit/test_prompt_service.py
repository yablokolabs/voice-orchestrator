"""Tests for PromptService."""

import pytest

from tests.conftest import InMemoryPromptRepository
from voice_orchestrator.domain.exceptions import PromptNotFoundError
from voice_orchestrator.services.prompt import PromptService


@pytest.fixture
def prompt_service() -> PromptService:
    return PromptService(repo=InMemoryPromptRepository())


class TestCreateVersion:
    async def test_first_version_is_one(self, prompt_service: PromptService):
        v = await prompt_service.create_version(
            prompt_id="p1",
            template="Extract actions: {{text}}",
            author="tester",
            change_reason="initial",
        )
        assert v.version == 1

    async def test_increments_version_number(self, prompt_service: PromptService):
        await prompt_service.create_version(
            prompt_id="p1", template="v1", author="a", change_reason="init"
        )
        v2 = await prompt_service.create_version(
            prompt_id="p1", template="v2", author="a", change_reason="update"
        )
        assert v2.version == 2


class TestActivate:
    async def test_activates_specified_version(self, prompt_service: PromptService):
        await prompt_service.create_version(
            prompt_id="p1", template="v1", author="a", change_reason="init"
        )
        await prompt_service.create_version(
            prompt_id="p1", template="v2", author="a", change_reason="update"
        )
        activated = await prompt_service.activate("p1", 2)
        assert activated.is_active is True
        assert activated.version == 2

    async def test_raises_when_version_not_found(self, prompt_service: PromptService):
        with pytest.raises(PromptNotFoundError):
            await prompt_service.activate("nonexistent", 99)


class TestRollback:
    async def test_reverts_to_previous_version(self, prompt_service: PromptService):
        await prompt_service.create_version(
            prompt_id="p1", template="v1", author="a", change_reason="init", activate=True
        )
        await prompt_service.create_version(
            prompt_id="p1", template="v2", author="a", change_reason="update", activate=True
        )
        rolled = await prompt_service.rollback("p1")
        assert rolled.version == 1
        assert rolled.is_active is True

    async def test_raises_when_no_previous_version(self, prompt_service: PromptService):
        await prompt_service.create_version(
            prompt_id="p1", template="v1", author="a", change_reason="init", activate=True
        )
        with pytest.raises(PromptNotFoundError, match="No previous version"):
            await prompt_service.rollback("p1")

    async def test_raises_when_no_active_version(self, prompt_service: PromptService):
        with pytest.raises(PromptNotFoundError, match="No active version"):
            await prompt_service.rollback("p1")
