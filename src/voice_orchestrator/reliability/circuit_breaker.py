"""Per-provider circuit breakers using pybreaker."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any

import pybreaker
import structlog

from voice_orchestrator.domain.exceptions import CircuitOpenError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger(__name__)

# Sentinel used internally to carry an async result through pybreaker.call()
_SENTINEL = object()


class CircuitBreakerWrapper:
    """Wraps an async callable with a pybreaker circuit breaker.

    ``pybreaker.CircuitBreaker.call_async`` depends on tornado, so we
    run the async function ourselves and then feed the outcome back
    through ``breaker.call()`` so pybreaker tracks successes / failures
    and manages state transitions correctly.
    """

    def __init__(self, breaker: pybreaker.CircuitBreaker, provider_name: str) -> None:
        self._breaker = breaker
        self._provider_name = provider_name

    @property
    def state(self) -> str:
        return self._breaker.current_state

    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run *func* through the circuit breaker.

        Raises ``CircuitOpenError`` when the breaker is open.
        """
        # Fast-path: if the circuit is open, reject immediately.
        if self._breaker.current_state == pybreaker.STATE_OPEN:
            await logger.awarning(
                "circuit_open",
                provider=self._provider_name,
                state=self._breaker.current_state,
            )
            raise CircuitOpenError(self._provider_name)

        # Execute the async call outside pybreaker.
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            # Record the failure with pybreaker so it can track the
            # fail counter and potentially trip the circuit.
            try:
                self._breaker.call(self._replay_error, exc)
            except pybreaker.CircuitBreakerError:
                pass  # circuit just tripped — we still raise the original error
            except Exception:
                pass  # _replay_error re-raises exc; swallow it here
            raise
        else:
            # Record the success so pybreaker can track it / close the circuit.
            with contextlib.suppress(pybreaker.CircuitBreakerError):
                self._breaker.call(self._replay_success, result)
            return result

    @staticmethod
    def _replay_error(exc: Exception) -> None:
        """Re-raise *exc* so pybreaker records a failure."""
        raise exc

    @staticmethod
    def _replay_success(value: Any) -> Any:
        """Return *value* so pybreaker records a success."""
        return value


class CircuitBreakerRegistry:
    """Manages one ``CircuitBreakerWrapper`` per provider name."""

    def __init__(
        self,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ) -> None:
        self._fail_max = fail_max
        self._reset_timeout = reset_timeout
        self._breakers: dict[str, CircuitBreakerWrapper] = {}
        self._lock = asyncio.Lock()

    def get(self, provider_name: str) -> CircuitBreakerWrapper:
        """Return (or create) the breaker for *provider_name*."""
        if provider_name not in self._breakers:
            breaker = pybreaker.CircuitBreaker(
                fail_max=self._fail_max,
                reset_timeout=self._reset_timeout,
                name=provider_name,
            )
            self._breakers[provider_name] = CircuitBreakerWrapper(breaker, provider_name)
        return self._breakers[provider_name]

    async def execute(
        self,
        provider_name: str,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Convenience: get-or-create a breaker and run *func* through it."""
        wrapper = self.get(provider_name)
        return await wrapper.execute(func, *args, **kwargs)
