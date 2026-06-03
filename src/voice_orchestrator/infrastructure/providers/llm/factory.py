"""Factory for creating LLM provider instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voice_orchestrator.infrastructure.providers.llm.anthropic_provider import AnthropicProvider
from voice_orchestrator.infrastructure.providers.llm.bedrock_provider import BedrockProvider
from voice_orchestrator.infrastructure.providers.llm.openai_provider import OpenAIProvider

if TYPE_CHECKING:
    from voice_orchestrator.config import Settings
    from voice_orchestrator.domain.interfaces.providers import LLMProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "bedrock": BedrockProvider,
}


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create(provider_name: str, settings: Settings) -> LLMProvider:
        """Create an LLMProvider by name.

        Args:
            provider_name: One of "openai", "anthropic", "bedrock".
            settings: Application settings containing API keys and model config.

        Returns:
            An initialised LLMProvider instance.

        Raises:
            ValueError: If the provider name is not recognised.
        """
        provider_cls = _PROVIDERS.get(provider_name.lower())
        if provider_cls is None:
            available = ", ".join(sorted(_PROVIDERS))
            raise ValueError(
                f"Unknown LLM provider '{provider_name}'. Available: {available}"
            )
        return provider_cls(settings)  # type: ignore[call-arg]
