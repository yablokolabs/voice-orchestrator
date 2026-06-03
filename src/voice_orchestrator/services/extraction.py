"""Extraction service — orchestrates LLM action extraction."""

from __future__ import annotations

import structlog

from voice_orchestrator.domain.interfaces.providers import LLMProvider
from voice_orchestrator.domain.interfaces.repositories import (
    ExtractionRepository,
    PromptRepository,
)
from voice_orchestrator.domain.models.core import ExtractionResult

logger = structlog.get_logger(__name__)

DEFAULT_SYSTEM_PROMPT = """\
You are an AI assistant that extracts structured actions from voice commands.

Given a transcript of a voice command, extract the intent and entities \
into a JSON object.

Supported intents: create_meeting, create_reminder, send_message, \
create_task, set_alarm, make_call, search, unknown

Output format (respond ONLY with this JSON, no other text):
{
  "actions": [
    {
      "intent": "<intent_type>",
      "person": "<person name or null>",
      "date": "<YYYY-MM-DD or null>",
      "time": "<HH:MM or null>",
      "message": "<message content or null>",
      "subject": "<subject or null>",
      "location": "<location or null>"
    }
  ]
}

If the command contains multiple actions, include all of them.
If you cannot determine an entity, set it to null.
Always use the most specific intent that matches."""


class ExtractionService:
    def __init__(
        self,
        provider: LLMProvider,
        extraction_repo: ExtractionRepository,
        prompt_repo: PromptRepository,
    ):
        self._provider = provider
        self._extraction_repo = extraction_repo
        self._prompt_repo = prompt_repo

    async def extract(
        self,
        transcript: str,
        transcription_id: str,
        prompt_id: str = "default",
    ) -> ExtractionResult:
        prompt_version = await self._prompt_repo.get_active(prompt_id)
        if prompt_version:
            system_prompt = prompt_version.template
            version_num = prompt_version.version
        else:
            system_prompt = DEFAULT_SYSTEM_PROMPT
            version_num = 0

        user_prompt = f"Extract actions from this voice command:\n\n\"{transcript}\""

        logger.info(
            "extracting_actions",
            provider=self._provider.name,
            transcription_id=transcription_id,
            prompt_id=prompt_id,
            prompt_version=version_num,
        )

        result = await self._provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        result.transcription_id = transcription_id
        result.raw_text = transcript
        result.prompt_id = prompt_id
        result.prompt_version = version_num

        saved = await self._extraction_repo.save(result)

        logger.info(
            "extraction_complete",
            provider=self._provider.name,
            extraction_id=saved.id,
            num_actions=len(saved.actions),
            latency_ms=saved.latency_ms,
            tokens=saved.input_tokens + saved.output_tokens,
        )

        return saved
