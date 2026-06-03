"""Resilient wrappers that compose timeout → circuit breaker → retry → provider."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import structlog

from voice_orchestrator.domain.exceptions import CircuitOpenError
from voice_orchestrator.domain.interfaces.providers import LLMProvider, SpeechProvider
from voice_orchestrator.reliability.dead_letter import DeadLetterEntry, DeadLetterQueue

if TYPE_CHECKING:
    from voice_orchestrator.domain.models.core import ExtractionResult, TranscriptionResult
    from voice_orchestrator.reliability.circuit_breaker import CircuitBreakerRegistry
    from voice_orchestrator.reliability.retry_policy import RetryPolicy
    from voice_orchestrator.reliability.timeout import TimeoutPolicy

logger = structlog.get_logger(__name__)


class ResilientSpeechProvider(SpeechProvider):
    """Wraps a ``SpeechProvider`` with timeout, circuit breaker, retry, and DLQ."""

    def __init__(
        self,
        provider: SpeechProvider,
        retry_policy: RetryPolicy,
        cb_registry: CircuitBreakerRegistry,
        timeout_policy: TimeoutPolicy,
        dlq: DeadLetterQueue,
    ) -> None:
        self._provider = provider
        self._retry = retry_policy
        self._cb_registry = cb_registry
        self._timeout = timeout_policy
        self._dlq = dlq

    @property
    def name(self) -> str:
        return self._provider.name

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs: Any,
    ) -> TranscriptionResult:
        async def _call() -> TranscriptionResult:
            return await self._provider.transcribe(audio_data, audio_format, language, **kwargs)

        async def _with_cb() -> TranscriptionResult:
            return await self._cb_registry.execute(self._provider.name, _call)

        async def _with_timeout() -> TranscriptionResult:
            return await self._timeout.execute(_with_cb, operation=f"{self.name}.transcribe")

        try:
            return await self._retry.execute(_with_timeout)
        except CircuitOpenError:
            raise
        except Exception as exc:
            await self._dlq.enqueue(
                DeadLetterEntry(
                    request_id=str(uuid.uuid4()),
                    provider=self._provider.name,
                    error=str(exc),
                    payload={
                        "method": "transcribe",
                        "audio_format": audio_format,
                        "language": language,
                        "audio_size": len(audio_data),
                    },
                )
            )
            raise


class ResilientLLMProvider(LLMProvider):
    """Wraps an ``LLMProvider`` with timeout, circuit breaker, retry, and DLQ."""

    def __init__(
        self,
        provider: LLMProvider,
        retry_policy: RetryPolicy,
        cb_registry: CircuitBreakerRegistry,
        timeout_policy: TimeoutPolicy,
        dlq: DeadLetterQueue,
    ) -> None:
        self._provider = provider
        self._retry = retry_policy
        self._cb_registry = cb_registry
        self._timeout = timeout_policy
        self._dlq = dlq

    @property
    def name(self) -> str:
        return self._provider.name

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ExtractionResult:
        async def _call() -> ExtractionResult:
            return await self._provider.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        async def _with_cb() -> ExtractionResult:
            return await self._cb_registry.execute(self._provider.name, _call)

        async def _with_timeout() -> ExtractionResult:
            return await self._timeout.execute(_with_cb, operation=f"{self.name}.generate")

        try:
            return await self._retry.execute(_with_timeout)
        except CircuitOpenError:
            raise
        except Exception as exc:
            await self._dlq.enqueue(
                DeadLetterEntry(
                    request_id=str(uuid.uuid4()),
                    provider=self._provider.name,
                    error=str(exc),
                    payload={
                        "method": "generate",
                        "prompt_length": len(prompt),
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
            )
            raise
