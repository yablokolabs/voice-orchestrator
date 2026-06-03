"""AssemblyAI speech-to-text provider."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import httpx

from voice_orchestrator.domain.exceptions import TranscriptionError
from voice_orchestrator.domain.interfaces.providers import SpeechProvider
from voice_orchestrator.domain.models.core import TranscriptionResult

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

_BASE_URL = "https://api.assemblyai.com/v2"

# AssemblyAI pricing: $0.00025 per second
_COST_PER_SECOND = 0.00025

_POLL_INTERVAL_SECONDS = 1.0
_MAX_POLL_ATTEMPTS = 300  # 5 minutes max wait


class AssemblyAIProvider(SpeechProvider):
    """Speech-to-text provider using AssemblyAI REST API (upload → transcribe → poll)."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.assemblyai_api_key
        self._timeout = settings.request_timeout

    @property
    def name(self) -> str:
        return "assemblyai"

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs,
    ) -> TranscriptionResult:
        headers = {"Authorization": self._api_key}

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Step 1: upload audio
                upload_url = await self._upload(client, headers, audio_data)

                # Step 2: request transcription
                transcript_id = await self._request_transcription(
                    client, headers, upload_url, language
                )

                # Step 3: poll for completion
                raw = await self._poll_result(client, headers, transcript_id)
        except TranscriptionError:
            raise
        except httpx.HTTPError as exc:
            raise TranscriptionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        transcript: str = raw.get("text", "") or ""
        confidence: float = raw.get("confidence", 0.0) or 0.0
        duration_seconds: float = (raw.get("audio_duration", 0) or 0)
        cost = duration_seconds * _COST_PER_SECOND

        return TranscriptionResult(
            audio_file_id="",
            transcript=transcript,
            confidence=confidence,
            provider=self.name,
            model="assemblyai-default",
            latency_ms=elapsed_ms,
            cost_usd=cost,
            word_count=len(transcript.split()) if transcript else 0,
            language=language,
            raw_response=raw,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _upload(
        self, client: httpx.AsyncClient, headers: dict[str, str], audio_data: bytes
    ) -> str:
        resp = await client.post(
            f"{_BASE_URL}/upload",
            headers={**headers, "Content-Type": "application/octet-stream"},
            content=audio_data,
        )
        resp.raise_for_status()
        upload_url: str | None = resp.json().get("upload_url")
        if not upload_url:
            raise TranscriptionError(self.name, "Upload did not return upload_url")
        return upload_url

    async def _request_transcription(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        audio_url: str,
        language: str,
    ) -> str:
        body: dict[str, Any] = {"audio_url": audio_url}
        if language != "en":
            body["language_code"] = language

        resp = await client.post(
            f"{_BASE_URL}/transcript",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        transcript_id: str | None = resp.json().get("id")
        if not transcript_id:
            raise TranscriptionError(self.name, "Transcript request did not return id")
        return transcript_id

    async def _poll_result(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        transcript_id: str,
    ) -> dict[str, Any]:
        for _ in range(_MAX_POLL_ATTEMPTS):
            resp = await client.get(
                f"{_BASE_URL}/transcript/{transcript_id}",
                headers=headers,
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            status = data.get("status")

            if status == "completed":
                return data
            if status == "error":
                error_msg = data.get("error", "Unknown error")
                raise TranscriptionError(self.name, f"Transcription failed: {error_msg}")

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        raise TranscriptionError(self.name, "Transcription polling timed out")
