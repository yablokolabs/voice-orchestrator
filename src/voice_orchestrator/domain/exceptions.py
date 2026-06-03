"""Custom exceptions for the voice orchestrator."""


class VoiceOrchestratorError(Exception):
    """Base exception for all voice orchestrator errors."""


class ProviderError(VoiceOrchestratorError):
    """Raised when a provider call fails."""

    def __init__(self, provider: str, message: str, original: Exception | None = None):
        self.provider = provider
        self.original = original
        super().__init__(f"[{provider}] {message}")


class TranscriptionError(ProviderError):
    """Raised when speech-to-text fails."""


class ExtractionError(ProviderError):
    """Raised when LLM extraction fails."""


class CircuitOpenError(VoiceOrchestratorError):
    """Raised when a circuit breaker is open."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Circuit breaker open for provider: {provider}")


class AllProvidersFailedError(VoiceOrchestratorError):
    """Raised when all providers in a fallback chain fail."""

    def __init__(self, errors: list[tuple[str, Exception]]):
        self.errors = errors
        detail = "; ".join(f"{name}: {err}" for name, err in errors)
        super().__init__(f"All providers failed: {detail}")


class AudioValidationError(VoiceOrchestratorError):
    """Raised when audio file validation fails."""


class PromptNotFoundError(VoiceOrchestratorError):
    """Raised when a prompt or version is not found."""


class EvaluationError(VoiceOrchestratorError):
    """Raised when evaluation fails."""


class TimeoutError(VoiceOrchestratorError):  # noqa: A001
    """Raised when an async call exceeds its deadline."""

    def __init__(self, timeout: float, operation: str = "") -> None:
        self.timeout = timeout
        self.operation = operation
        msg = f"Operation timed out after {timeout}s"
        if operation:
            msg = f"{operation}: {msg}"
        super().__init__(msg)


class DeadLetterError(VoiceOrchestratorError):
    """Raised for dead-letter queue operations."""
