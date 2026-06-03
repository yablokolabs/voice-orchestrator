"""Pipeline router — transcription, extraction, and full pipeline."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from voice_orchestrator.api.schemas import (
    ExtractActionsRequest,
    ExtractionResponse,
    TranscribeRequest,
    TranscriptionResponse,
)

router = APIRouter(tags=["pipeline"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(request: TranscribeRequest) -> TranscriptionResponse:
    """Transcribe an audio file to text."""
    # In production, this would use DI to get the TranscriptionService
    # with the configured provider. Placeholder for DI wiring.
    raise HTTPException(status_code=501, detail="Requires configured STT provider")


@router.post("/extract-actions", response_model=ExtractionResponse)
async def extract_actions(request: ExtractActionsRequest) -> ExtractionResponse:
    """Extract structured actions from text or audio."""
    if not request.text and not request.audio_file_id:
        raise HTTPException(
            status_code=400, detail="Either 'text' or 'audio_file_id' must be provided"
        )
    raise HTTPException(status_code=501, detail="Requires configured LLM provider")
