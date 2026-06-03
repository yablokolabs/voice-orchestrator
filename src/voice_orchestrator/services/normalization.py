"""Normalization service — cleans transcripts before LLM extraction."""

from __future__ import annotations

import re


class NormalizationService:
    """Cleans and normalizes raw transcripts for consistent LLM input."""

    FILLER_WORDS = {
        "um", "uh", "er", "ah", "like", "you know", "i mean",
        "basically", "actually", "literally", "right", "so yeah",
    }

    FILLER_PATTERN = re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in FILLER_WORDS) + r")\b",
        re.IGNORECASE,
    )

    def normalize(self, transcript: str) -> str:
        text = transcript.strip()
        if not text:
            return text

        text = self._remove_fillers(text)
        text = self._collapse_whitespace(text)
        text = self._fix_punctuation(text)
        text = self._capitalize_sentences(text)

        return text.strip()

    def _remove_fillers(self, text: str) -> str:
        return self.FILLER_PATTERN.sub("", text)

    def _collapse_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text)

    def _fix_punctuation(self, text: str) -> str:
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.,!?;:]){2,}", r"\1", text)
        return text

    def _capitalize_sentences(self, text: str) -> str:
        sentences = re.split(r"([.!?]\s+)", text)
        result = []
        for i, segment in enumerate(sentences):
            if i == 0 or (i > 0 and re.match(r"[.!?]\s+", sentences[i - 1])):
                segment = segment[:1].upper() + segment[1:] if segment else segment
            result.append(segment)
        return "".join(result)
