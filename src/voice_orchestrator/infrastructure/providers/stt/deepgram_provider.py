"""Deepgram speech-to-text provider."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import httpx

from voice_orchestrator.domain.exceptions import TranscriptionError
from voice_orchestrator.domain.interfaces.providers import SpeechProvider
from voice_orchestrator.domain.models.core import TranscriptionResult

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings

_DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"

# Nova-2 pricing: $0.0043 per minute
_COST_PER_MINUTE = 0.0043

_CONTENT_TYPES: dict[str, str] = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "webm": "audio/webm",
}


class DeepgramProvider(SpeechProvider):
    """Speech-to-text provider using Deepgram REST API."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.deepgram_api_key
        self._model = settings.deepgram_model
        self._timeout = settings.request_timeout

    @property
    def name(self) -> str:
        return "deepgram"

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str = "en",
        **kwargs,
    ) -> TranscriptionResult:
        content_type = _CONTENT_TYPES.get(audio_format, f"audio/{audio_format}")
        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": content_type,
        }
        params = {
            "model": self._model,
            "language": language,
            "punctuate": "true",
        }

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    _DEEPGRAM_API_URL,
                    headers=headers,
                    params=params,
                    content=audio_data,
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TranscriptionError(self.name, str(exc), original=exc) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw: dict[str, Any] = resp.json()
        result = _parse_response(raw)
        duration_seconds = result["duration"]
        cost = (duration_seconds / 60.0) * _COST_PER_MINUTE

        return TranscriptionResult(
            audio_file_id="",
            transcript=result["transcript"],
            confidence=result["confidence"],
            provider=self.name,
            model=self._model,
            latency_ms=elapsed_ms,
            cost_usd=cost,
            word_count=len(result["transcript"].split()) if result["transcript"] else 0,
            language=language,
            raw_response=raw,
        )


def _parse_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract transcript, confidence, and duration from Deepgram response."""
    try:
        results = raw["results"]
        channels = results["channels"]
        first_alt = channels[0]["alternatives"][0]
        transcript: str = first_alt.get("transcript", "")
        confidence: float = first_alt.get("confidence", 0.0)
        duration: float = raw.get("metadata", {}).get("duration", 0.0)
    except (KeyError, IndexError) as exc:
        raise TranscriptionError("deepgram", f"Unexpected response structure: {exc}") from exc
    return {"transcript": transcript, "confidence": confidence, "duration": duration}
