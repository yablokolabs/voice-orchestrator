"""Factory for creating STT provider instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voice_orchestrator.infrastructure.providers.stt.assemblyai_provider import AssemblyAIProvider
from voice_orchestrator.infrastructure.providers.stt.deepgram_provider import DeepgramProvider
from voice_orchestrator.infrastructure.providers.stt.whisper_provider import WhisperProvider

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings
    from voice_orchestrator.domain.interfaces.providers import SpeechProvider

_PROVIDERS: dict[str, type[SpeechProvider]] = {
    "whisper": WhisperProvider,
    "deepgram": DeepgramProvider,
    "assemblyai": AssemblyAIProvider,
}


class STTProviderFactory:
    """Factory for creating speech-to-text provider instances."""

    @staticmethod
    def create(provider_name: str, settings: Settings) -> SpeechProvider:
        """Create a SpeechProvider by name.

        Args:
            provider_name: One of "whisper", "deepgram", "assemblyai".
            settings: Application settings containing API keys and model config.

        Returns:
            An initialised SpeechProvider instance.

        Raises:
            ValueError: If the provider name is not recognised.
        """
        provider_cls = _PROVIDERS.get(provider_name.lower())
        if provider_cls is None:
            available = ", ".join(sorted(_PROVIDERS))
            raise ValueError(
                f"Unknown STT provider '{provider_name}'. Available: {available}"
            )
        return provider_cls(settings)
