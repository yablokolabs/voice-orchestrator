from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VO_", case_sensitive=False)

    app_name: str = "voice-orchestrator"
    debug: bool = False
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_orchestrator"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Storage
    upload_dir: Path = Path("uploads")
    max_audio_size_mb: int = 50
    allowed_audio_formats: list[str] = Field(
        default_factory=lambda: ["wav", "mp3", "m4a", "ogg", "flac", "webm"]
    )

    # STT Providers
    default_stt_provider: str = "whisper"
    whisper_api_key: str = ""
    whisper_model: str = "whisper-1"
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-2"
    assemblyai_api_key: str = ""

    # LLM Providers
    default_llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"

    # Reliability
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60
    request_timeout: float = 30.0

    # Observability
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "voice-orchestrator"
    prometheus_port: int = 9090

    # Evaluation
    golden_dataset_dir: Path = Path("golden_dataset")

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "voice-orchestrator"


@lru_cache
def get_settings() -> Settings:
    return Settings()
