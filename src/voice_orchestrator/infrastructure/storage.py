"""Local filesystem audio storage."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles

from voice_orchestrator.domain.interfaces.providers import AudioStorage


class LocalAudioStorage(AudioStorage):
    def __init__(self, upload_dir: Path):
        self._upload_dir = upload_dir
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def store(self, audio_data: bytes, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "wav"
        storage_name = f"{uuid.uuid4()}.{ext}"
        path = self._upload_dir / storage_name

        async with aiofiles.open(path, "wb") as f:
            await f.write(audio_data)

        return str(path)

    async def retrieve(self, storage_path: str) -> bytes:
        async with aiofiles.open(storage_path, "rb") as f:
            return await f.read()  # type: ignore[no-any-return]

    async def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            os.remove(path)
