"""Celery application configuration."""

from __future__ import annotations

from celery import Celery

from voice_orchestrator.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "voice_orchestrator",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "voice_orchestrator.tasks.*": {"queue": "default"},
        },
    )

    app.autodiscover_tasks(["voice_orchestrator.tasks"])

    return app


celery_app = create_celery_app()
