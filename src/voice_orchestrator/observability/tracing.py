"""OpenTelemetry instrumentation setup for the voice orchestrator."""

from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from voice_orchestrator.config import Settings


def setup_telemetry(settings: Settings) -> None:
    """Initialize OpenTelemetry tracing."""
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "0.1.0",
            "deployment.environment": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


def instrument_fastapi(app: Any) -> None:
    """Instrument FastAPI app with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx() -> None:
    """Instrument httpx client calls."""
    HTTPXClientInstrumentor().instrument()


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument SQLAlchemy engine."""
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def get_tracer(name: str = "voice_orchestrator") -> trace.Tracer:
    """Get a tracer instance for manual span creation."""
    return trace.get_tracer(name)
