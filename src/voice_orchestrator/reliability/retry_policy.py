"""Retry policy with tenacity, structured logging, and metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger(__name__)


class RetryPolicy:
    """Wraps an async callable with configurable tenacity retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        jitter: float = 1.0,
        retry_on: tuple[type[BaseException], ...] = (Exception,),
    ) -> None:
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.jitter = jitter
        self.retry_on = retry_on

        # Simple counters for observability
        self.total_retries: int = 0
        self.total_successes: int = 0
        self.total_failures: int = 0

    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute *func* with retries.

        Returns the result on success.  On exhaustion re-raises the last
        exception after logging.
        """
        attempt_number = 0
        last_exception: BaseException | None = None

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries + 1),
                wait=wait_exponential_jitter(
                    initial=self.backoff_base,
                    max=self.backoff_max,
                    jitter=self.jitter,
                ),
                retry=retry_if_exception_type(self.retry_on),
                reraise=True,
            ):
                with attempt:
                    attempt_number = attempt.retry_state.attempt_number
                    if attempt_number > 1:
                        self.total_retries += 1
                        await logger.awarning(
                            "retry_attempt",
                            attempt=attempt_number,
                            max_retries=self.max_retries,
                            func=getattr(func, "__qualname__", str(func)),
                        )
                    result = await func(*args, **kwargs)

            self.total_successes += 1
            if attempt_number > 1:
                await logger.ainfo(
                    "retry_succeeded",
                    attempts=attempt_number,
                    func=getattr(func, "__qualname__", str(func)),
                )
            return result  # noqa: TRY300

        except RetryError as exc:
            last_exception = exc.last_attempt.exception()
            self.total_failures += 1
            await logger.aerror(
                "retry_exhausted",
                attempts=attempt_number,
                max_retries=self.max_retries,
                func=getattr(func, "__qualname__", str(func)),
                error=str(last_exception),
            )
            raise last_exception from exc  # type: ignore[misc]

        except Exception as exc:
            # Non-retryable or first-attempt failure
            last_exception = exc
            self.total_failures += 1
            await logger.aerror(
                "retry_failed",
                attempts=attempt_number,
                func=getattr(func, "__qualname__", str(func)),
                error=str(exc),
            )
            raise
