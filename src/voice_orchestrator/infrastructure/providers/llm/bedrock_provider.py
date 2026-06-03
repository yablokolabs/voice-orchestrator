"""AWS Bedrock LLM provider for intent extraction."""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from voice_orchestrator.domain.exceptions import ExtractionError
from voice_orchestrator.domain.interfaces.providers import LLMProvider
from voice_orchestrator.domain.models.core import Action, ExtractionResult, IntentType

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

# Default Claude Sonnet on Bedrock pricing (per 1M tokens)
_INPUT_COST_PER_M = 3.00
_OUTPUT_COST_PER_M = 15.00


class BedrockProvider(LLMProvider):
    """LLM provider using AWS Bedrock invoke_model (runs sync client in executor)."""

    def __init__(self, settings: Settings) -> None:
        self._model_id = settings.bedrock_model_id
        self._client = boto3.client("bedrock-runtime", region_name=settings.bedrock_region)

    @property
    def name(self) -> str:
        return "bedrock"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> ExtractionResult:
        body = self._build_request_body(prompt, system_prompt, temperature, max_tokens)

        start = time.perf_counter()
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.invoke_model(
                    modelId=self._model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body),
                ),
            )
        except (BotoCoreError, ClientError) as exc:
            raise ExtractionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw = self._parse_response_body(response)
        raw_text = self._extract_text(raw)

        input_tokens = raw.get("usage", {}).get("input_tokens", 0)
        output_tokens = raw.get("usage", {}).get("output_tokens", 0)

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
            model=self._model_id,
            prompt_id="",
            prompt_version=0,
            latency_ms=elapsed_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            raw_response=raw,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_request_body(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build the Anthropic Messages-format body used by Bedrock Claude models."""
        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt
        return body

    @staticmethod
    def _parse_response_body(response: dict[str, Any]) -> dict[str, Any]:
        try:
            return json.loads(response["body"].read())
        except (KeyError, json.JSONDecodeError) as exc:
            raise ExtractionError("bedrock", f"Failed to parse response body: {exc}") from exc

    @staticmethod
    def _extract_text(raw: dict[str, Any]) -> str:
        content = raw.get("content", [])
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)


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
