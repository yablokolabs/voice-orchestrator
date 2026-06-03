"""Pipeline service — end-to-end voice-to-action orchestration."""

from __future__ import annotations

import time

import structlog

from voice_orchestrator.domain.interfaces.repositories import PipelineResultRepository
from voice_orchestrator.domain.models.core import PipelineResult, ProcessingStatus
from voice_orchestrator.services.audio import AudioService
from voice_orchestrator.services.extraction import ExtractionService
from voice_orchestrator.services.transcription import TranscriptionService

logger = structlog.get_logger(__name__)


class PipelineService:
    def __init__(
        self,
        audio_service: AudioService,
        transcription_service: TranscriptionService,
        extraction_service: ExtractionService,
        pipeline_repo: PipelineResultRepository,
    ):
        self._audio = audio_service
        self._transcription = transcription_service
        self._extraction = extraction_service
        self._pipeline_repo = pipeline_repo

    async def process(
        self,
        audio_file_id: str,
        stt_provider: str | None = None,
        llm_provider: str | None = None,
        prompt_id: str = "default",
    ) -> PipelineResult:
        start = time.perf_counter()

        logger.info("pipeline_start", audio_file_id=audio_file_id)

        audio_data = await self._audio.get_audio_data(audio_file_id)
        audio_file = await self._audio.get(audio_file_id)

        transcription = await self._transcription.transcribe(
            audio_data=audio_data,
            audio_file_id=audio_file_id,
            audio_format=audio_file.format if audio_file else "wav",
        )

        extraction = await self._extraction.extract(
            transcript=transcription.transcript,
            transcription_id=transcription.id,
            prompt_id=prompt_id,
        )

        total_latency = (time.perf_counter() - start) * 1000
        total_cost = transcription.cost_usd + extraction.cost_usd

        result = PipelineResult(
            audio_file_id=audio_file_id,
            transcription=transcription,
            extraction=extraction,
            status=ProcessingStatus.COMPLETED,
            total_latency_ms=total_latency,
            total_cost_usd=total_cost,
        )

        saved = await self._pipeline_repo.save(result)

        logger.info(
            "pipeline_complete",
            pipeline_id=saved.id,
            audio_file_id=audio_file_id,
            total_latency_ms=total_latency,
            total_cost_usd=total_cost,
            num_actions=len(extraction.actions),
        )

        return saved
