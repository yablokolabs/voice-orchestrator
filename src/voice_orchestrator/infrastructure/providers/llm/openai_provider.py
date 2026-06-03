"""OpenAI LLM provider for intent extraction."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

import openai

from voice_orchestrator.domain.exceptions import ExtractionError
from voice_orchestrator.domain.interfaces.providers import LLMProvider
from voice_orchestrator.domain.models.core import Action, ExtractionResult, IntentType

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

# GPT-4o pricing (per 1M tokens)
_INPUT_COST_PER_M = 2.50
_OUTPUT_COST_PER_M = 10.00


class OpenAIProvider(LLMProvider):
    """LLM provider using OpenAI chat completions."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> ExtractionResult:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except openai.OpenAIError as exc:
            raise ExtractionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw: dict[str, Any] = response.model_dump()
        raw_text = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        cost = (
            (input_tokens / 1_000_000) * _INPUT_COST_PER_M
            + (output_tokens / 1_000_000) * _OUTPUT_COST_PER_M
        )

        actions = _parse_actions(raw_text)

        return ExtractionResult(
            transcription_id="",
            actions=actions,
            raw_text=raw_text,
            provider=self.name,
            model=self._model,
            prompt_id="",
            prompt_version=0,
            latency_ms=elapsed_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            raw_response=raw,
        )


def _parse_actions(raw_text: str) -> list[Action]:
    """Defensively parse LLM JSON output into Action objects."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return [Action(intent=IntentType.UNKNOWN, extra={"raw": raw_text})]

    if isinstance(data, dict):
        actions_data = data.get("actions", [data])
    elif isinstance(data, list):
        actions_data = data
    else:
        return [Action(intent=IntentType.UNKNOWN, extra={"raw": raw_text})]

    actions: list[Action] = []
    for item in actions_data:
        if not isinstance(item, dict):
            continue
        intent_str = item.get("intent", "unknown")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN
        actions.append(
            Action(
                intent=intent,
                person=item.get("person"),
                date=item.get("date"),
                time=item.get("time"),
                message=item.get("message"),
                subject=item.get("subject"),
                location=item.get("location"),
                extra={k: v for k, v in item.items() if k not in Action.model_fields},
            )
        )
    return actions or [Action(intent=IntentType.UNKNOWN)]
