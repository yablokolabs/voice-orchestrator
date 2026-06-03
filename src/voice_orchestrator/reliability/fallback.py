"""Fallback chain — tries providers in order until one succeeds."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

import structlog

from voice_orchestrator.domain.exceptions import AllProvidersFailedError, CircuitOpenError

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class FallbackChain(Generic[T]):
    """Tries an ordered list of providers; on failure moves to the next.

    ``T`` is expected to be ``SpeechProvider`` or ``LLMProvider`` (any object
    with a ``.name`` attribute and async methods).
    """

    def __init__(self, providers: list[T]) -> None:
        if not providers:
            raise ValueError("FallbackChain requires at least one provider")
        self._providers = providers

    async def execute(self, func_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call *func_name* on each provider until one succeeds.

        Raises ``AllProvidersFailedError`` when every provider fails.
        """
        failures: list[tuple[str, Exception]] = []

        for provider in self._providers:
            name = getattr(provider, "name", type(provider).__name__)
            method = getattr(provider, func_name, None)
            if method is None:
                exc = AttributeError(f"Provider '{name}' has no method '{func_name}'")
                failures.append((name, exc))
                await logger.awarning(
                    "fallback_skip_missing_method",
                    provider=name,
                    method=func_name,
                )
                continue

            try:
                result = await method(*args, **kwargs)
                if failures:
                    await logger.ainfo(
                        "fallback_succeeded",
                        provider=name,
                        method=func_name,
                        previous_failures=[f[0] for f in failures],
                    )
                return result  # noqa: TRY300

            except CircuitOpenError as exc:
                failures.append((name, exc))
                await logger.awarning(
                    "fallback_circuit_open",
                    provider=name,
                    method=func_name,
                )

            except Exception as exc:
                failures.append((name, exc))
                await logger.awarning(
                    "fallback_provider_failed",
                    provider=name,
                    method=func_name,
                    error=str(exc),
                )

        raise AllProvidersFailedError(failures)
