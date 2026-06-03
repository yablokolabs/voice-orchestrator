"""FastAPI dependency injection — wires services to providers and repos."""

from __future__ import annotations

from functools import lru_cache

from voice_orchestrator.config import Settings, get_settings


@lru_cache
def get_settings_dep() -> Settings:
    return get_settings()
