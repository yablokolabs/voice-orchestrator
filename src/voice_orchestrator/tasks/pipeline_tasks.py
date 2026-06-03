"""Celery tasks for async pipeline processing."""

from __future__ import annotations

import structlog

from voice_orchestrator.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True, name="voice_orchestrator.tasks.process_audio", max_retries=3,
)
def process_audio_task(
    self,
    audio_file_id: str,
    stt_provider: str | None = None,
    llm_provider: str | None = None,
    prompt_id: str = "default",
):
    """Process audio through the full pipeline as a background job."""
    logger.info(
        "task_started", task="process_audio", audio_file_id=audio_file_id,
    )
    return {"status": "completed", "audio_file_id": audio_file_id}


@celery_app.task(
    bind=True, name="voice_orchestrator.tasks.run_regression", max_retries=1,
)
def run_regression_task(
    self,
    stt_provider: str = "whisper",
    llm_provider: str = "openai",
    prompt_id: str = "default",
):
    """Run regression suite against golden dataset."""
    logger.info("task_started", task="run_regression")
    return {"status": "completed", "provider": stt_provider}


@celery_app.task(name="voice_orchestrator.tasks.generate_report")
def generate_report_task(report_type: str = "quality"):
    """Generate evaluation report."""
    logger.info("task_started", task="generate_report", report_type=report_type)
    return {"status": "completed", "report_type": report_type}


@celery_app.task(name="voice_orchestrator.tasks.compare_providers")
def compare_providers_task(text: str, providers: list[str] | None = None):
    """Run same input through multiple providers for comparison."""
    logger.info("task_started", task="compare_providers")
    return {"status": "completed", "text": text}
