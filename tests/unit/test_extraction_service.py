"""Tests for ExtractionService."""

import pytest

from tests.conftest import (
    FakeLLMProvider,
    InMemoryExtractionRepository,
    InMemoryPromptRepository,
)
from voice_orchestrator.domain.models.core import Action, IntentType
from voice_orchestrator.services.extraction import ExtractionService


@pytest.fixture
def extraction_service() -> ExtractionService:
    actions = [Action(intent=IntentType.SEND_MESSAGE, person="Bob", message="hi")]
    provider = FakeLLMProvider(actions=actions)
    extraction_repo = InMemoryExtractionRepository()
    prompt_repo = InMemoryPromptRepository()
    return ExtractionService(
        provider=provider,
        extraction_repo=extraction_repo,
        prompt_repo=prompt_repo,
    )


class TestExtract:
    async def test_sets_transcription_id(self, extraction_service: ExtractionService):
        result = await extraction_service.extract(
            transcript="send hi to Bob",
            transcription_id="tx-100",
        )
        assert result.transcription_id == "tx-100"

    async def test_sets_raw_text(self, extraction_service: ExtractionService):
        result = await extraction_service.extract(
            transcript="send hi to Bob",
            transcription_id="tx-101",
        )
        assert result.raw_text == "send hi to Bob"

    async def test_sets_prompt_info(self, extraction_service: ExtractionService):
        result = await extraction_service.extract(
            transcript="send hi to Bob",
            transcription_id="tx-102",
            prompt_id="default",
        )
        assert result.prompt_id == "default"
        # No active version in empty repo, so fallback version 0
        assert result.prompt_version == 0

    async def test_returns_actions_from_provider(self, extraction_service: ExtractionService):
        result = await extraction_service.extract(
            transcript="send hi to Bob",
            transcription_id="tx-103",
        )
        assert len(result.actions) == 1
        assert result.actions[0].intent == IntentType.SEND_MESSAGE
        assert result.actions[0].person == "Bob"

    async def test_saves_to_repository(self):
        provider = FakeLLMProvider()
        extraction_repo = InMemoryExtractionRepository()
        prompt_repo = InMemoryPromptRepository()
        service = ExtractionService(
            provider=provider,
            extraction_repo=extraction_repo,
            prompt_repo=prompt_repo,
        )
        result = await service.extract(transcript="test", transcription_id="tx-200")
        stored = await extraction_repo.get_by_id(result.id)
        assert stored is not None
        assert stored.id == result.id
