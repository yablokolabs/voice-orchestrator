"""Anthropic LLM provider for intent extraction."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

import anthropic

from voice_orchestrator.domain.exceptions import ExtractionError
from voice_orchestrator.domain.interfaces.providers import LLMProvider
from voice_orchestrator.domain.models.core import Action, ExtractionResult, IntentType

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

# Claude Sonnet pricing (per 1M tokens)
_INPUT_COST_PER_M = 3.00
_OUTPUT_COST_PER_M = 15.00


class AnthropicProvider(LLMProvider):
    """LLM provider using Anthropic Messages API."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.anthropic_model
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> ExtractionResult:
        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            request_kwargs["system"] = system_prompt

        start = time.perf_counter()
        try:
            response = await self._client.messages.create(**request_kwargs)
        except anthropic.AnthropicError as exc:
            raise ExtractionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw: dict[str, Any] = response.model_dump()
        raw_text = ""
        for block in response.content:
            if block.type == "text":
                raw_text += block.text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

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
