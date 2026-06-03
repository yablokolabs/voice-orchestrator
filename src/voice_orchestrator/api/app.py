"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voice_orchestrator.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer()
                if settings.debug
                else structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(),
        )
        logger = structlog.get_logger()
        logger.info("starting_app", environment=settings.environment)

        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        yield

        logger.info("shutting_down_app")

    app = FastAPI(
        title="Voice Orchestrator",
        description="Production-grade Voice-to-Action AI Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from voice_orchestrator.api.routers import (
        audio,
        evaluation,
        feedback,
        health,
        pipeline,
        prompts,
    )

    prefix = settings.api_prefix
    app.include_router(health.router)
    app.include_router(audio.router, prefix=prefix)
    app.include_router(pipeline.router, prefix=prefix)
    app.include_router(evaluation.router, prefix=prefix)
    app.include_router(prompts.router, prefix=prefix)
    app.include_router(feedback.router, prefix=prefix)

    return app
