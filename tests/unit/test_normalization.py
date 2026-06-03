"""Tests for NormalizationService."""

import pytest

from voice_orchestrator.services.normalization import NormalizationService


@pytest.fixture
def normalizer() -> NormalizationService:
    return NormalizationService()


class TestNormalize:
    def test_removes_filler_words(self, normalizer: NormalizationService):
        result = normalizer.normalize("I um want to uh schedule a meeting")
        assert "um" not in result.lower().split()
        assert "uh" not in result.lower().split()
        assert "schedule" in result.lower()
        assert "meeting" in result.lower()

    def test_removes_like_filler(self, normalizer: NormalizationService):
        result = normalizer.normalize("can you like send a message")
        assert "send" in result.lower()
        assert "message" in result.lower()
        # "like" as a filler should be removed
        assert "like" not in result.lower().split()

    def test_removes_you_know_filler(self, normalizer: NormalizationService):
        result = normalizer.normalize("you know I need a reminder")
        assert "reminder" in result.lower()

    def test_collapses_whitespace(self, normalizer: NormalizationService):
        result = normalizer.normalize("hello    world   test")
        assert "  " not in result

    def test_capitalizes_sentences(self, normalizer: NormalizationService):
        result = normalizer.normalize("hello world. this is a test")
        assert result[0].isupper()
        # After period, next sentence should be capitalized
        parts = result.split(". ")
        if len(parts) > 1:
            assert parts[1][0].isupper()

    def test_handles_empty_string(self, normalizer: NormalizationService):
        result = normalizer.normalize("")
        assert result == ""

    def test_handles_whitespace_only(self, normalizer: NormalizationService):
        result = normalizer.normalize("   ")
        assert result == ""

    def test_handles_string_with_only_fillers(self, normalizer: NormalizationService):
        result = normalizer.normalize("um uh like")
        # After removing fillers and collapsing whitespace, should be empty or near-empty
        assert result.strip() == ""
