"""In-memory dead-letter queue for failed requests."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DeadLetterEntry:
    """A single failed request record."""

    request_id: str
    provider: str
    error: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class DeadLetterQueue:
    """Simple in-memory DLQ backed by a list.

    The interface is designed so the backing store can be swapped to
    Redis / Postgres later without changing callers.
    """

    def __init__(self) -> None:
        self._entries: list[DeadLetterEntry] = []
        self._lock = asyncio.Lock()

    async def enqueue(self, entry: DeadLetterEntry) -> None:
        """Append a failed-request entry."""
        async with self._lock:
            self._entries.append(entry)
        await logger.ainfo(
            "dlq_enqueued",
            entry_id=entry.id,
            request_id=entry.request_id,
            provider=entry.provider,
            error=entry.error,
        )

    async def list_entries(self, limit: int = 100) -> list[DeadLetterEntry]:
        """Return the most recent *limit* entries (newest first)."""
        async with self._lock:
            return list(reversed(self._entries[-limit:]))

    async def retry(self, entry_id: str) -> DeadLetterEntry | None:
        """Remove and return the entry for retry, incrementing its counter.

        Returns ``None`` if the entry is not found.
        """
        async with self._lock:
            for i, entry in enumerate(self._entries):
                if entry.id == entry_id:
                    entry = self._entries.pop(i)
                    entry.retry_count += 1
                    await logger.ainfo(
                        "dlq_retry",
                        entry_id=entry.id,
                        retry_count=entry.retry_count,
                    )
                    return entry
        return None

    async def remove(self, entry_id: str) -> bool:
        """Remove an entry without retrying. Returns ``True`` if found."""
        async with self._lock:
            for i, entry in enumerate(self._entries):
                if entry.id == entry_id:
                    self._entries.pop(i)
                    await logger.ainfo("dlq_removed", entry_id=entry_id)
                    return True
        return False

    async def size(self) -> int:
        async with self._lock:
            return len(self._entries)
