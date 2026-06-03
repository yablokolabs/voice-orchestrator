"""Audio router — upload and retrieve audio files."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from voice_orchestrator.api.schemas import AudioUploadResponse
from voice_orchestrator.config import get_settings
from voice_orchestrator.domain.models.core import AudioFile, AudioFormat
from voice_orchestrator.infrastructure.storage import LocalAudioStorage

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio(file: UploadFile):
    """Upload an audio file for processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    audio_data = await file.read()

    settings = get_settings()
    storage = LocalAudioStorage(settings.upload_dir)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {settings.allowed_audio_formats}",
        )

    size_mb = len(audio_data) / (1024 * 1024)
    if size_mb > settings.max_audio_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max: {settings.max_audio_size_mb}MB",
        )

    storage_path = await storage.store(audio_data, file.filename)

    audio_file = AudioFile(
        filename=file.filename,
        format=AudioFormat(ext),
        size_bytes=len(audio_data),
        storage_path=storage_path,
    )

    return AudioUploadResponse(
        audio_file_id=audio_file.id,
        filename=audio_file.filename,
        format=audio_file.format,
        size_bytes=audio_file.size_bytes,
        uploaded_at=audio_file.uploaded_at,
    )
