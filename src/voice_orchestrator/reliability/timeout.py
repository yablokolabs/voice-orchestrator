"""Async timeout policy."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from voice_orchestrator.domain.exceptions import TimeoutError as VoiceTimeoutError  # noqa: A004

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger(__name__)


class TimeoutPolicy:
    """Wraps async calls with ``asyncio.wait_for``."""

    def __init__(self, timeout: float = 30.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout

    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        operation: str = "",
        **kwargs: Any,
    ) -> Any:
        """Run *func* with an asyncio timeout.

        Raises ``VoiceTimeoutError`` if the deadline is exceeded.
        """
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
        except asyncio.TimeoutError:  # noqa: UP041
            await logger.aerror(
                "timeout_exceeded",
                timeout=self.timeout,
                operation=operation or getattr(func, "__qualname__", str(func)),
            )
            raise VoiceTimeoutError(self.timeout, operation) from None
