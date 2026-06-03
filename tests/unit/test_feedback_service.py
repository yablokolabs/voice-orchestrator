"""Tests for FeedbackService."""

import pytest

from tests.conftest import InMemoryExtractionRepository, InMemoryFeedbackRepository
from voice_orchestrator.domain.models.core import (
    Action,
    ExtractionResult,
    FeedbackStatus,
    IntentType,
)
from voice_orchestrator.services.feedback import FeedbackService


def _seed_extraction(repo: InMemoryExtractionRepository, extraction_id: str = "ex-1") -> str:
    """Synchronously insert an extraction so the service can find it."""
    extraction = ExtractionResult(
        id=extraction_id,
        transcription_id="tx-1",
        actions=[Action(intent=IntentType.CREATE_MEETING, person="Alice")],
        raw_text="test",
        provider="fake",
        model="fake",
        prompt_id="default",
        prompt_version=1,
        latency_ms=10.0,
        input_tokens=10,
        output_tokens=10,
        cost_usd=0.001,
    )
    repo._store[extraction.id] = extraction
    return extraction.id


@pytest.fixture
def repos():
    feedback_repo = InMemoryFeedbackRepository()
    extraction_repo = InMemoryExtractionRepository()
    return feedback_repo, extraction_repo


@pytest.fixture
def feedback_service(repos):
    feedback_repo, extraction_repo = repos
    return FeedbackService(feedback_repo=feedback_repo, extraction_repo=extraction_repo)


class TestSubmit:
    async def test_creates_feedback_linked_to_extraction(self, feedback_service, repos):
        feedback_repo, extraction_repo = repos
        ext_id = _seed_extraction(extraction_repo)

        fb = await feedback_service.submit(
            extraction_id=ext_id,
            status=FeedbackStatus.APPROVED,
            reviewer="human-1",
        )
        assert fb.extraction_id == ext_id
        assert fb.status == FeedbackStatus.APPROVED
        assert fb.reviewer == "human-1"

    async def test_raises_for_missing_extraction(self, feedback_service):
        with pytest.raises(ValueError, match="Extraction not found"):
            await feedback_service.submit(
                extraction_id="nonexistent",
                status=FeedbackStatus.APPROVED,
            )


class TestGetReviewQueue:
    async def test_returns_pending_items(self, feedback_service, repos):
        feedback_repo, extraction_repo = repos
        ext_id = _seed_extraction(extraction_repo)

        await feedback_service.submit(ext_id, FeedbackStatus.PENDING, reviewer="r1")

        queue = await feedback_service.get_review_queue()
        assert len(queue) == 1
        assert queue[0].status == FeedbackStatus.PENDING


class TestComputeAgreementRate:
    async def test_returns_correct_rates(self, repos):
        feedback_repo, extraction_repo = repos
        service = FeedbackService(feedback_repo=feedback_repo, extraction_repo=extraction_repo)

        ext_id1 = _seed_extraction(extraction_repo, "ex-a")
        ext_id2 = _seed_extraction(extraction_repo, "ex-b")
        ext_id3 = _seed_extraction(extraction_repo, "ex-c")

        await service.submit(ext_id1, FeedbackStatus.APPROVED, reviewer="r1")
        await service.submit(ext_id2, FeedbackStatus.APPROVED, reviewer="r2")
        await service.submit(ext_id3, FeedbackStatus.REJECTED, reviewer="r3")

        rates = await service.compute_agreement_rate()
        assert rates["total_reviewed"] == 3
        assert rates["approved"] == 2
        assert rates["rejected"] == 1
        assert abs(rates["agreement_rate"] - 2.0 / 3.0) < 0.01

    async def test_returns_zero_when_no_reviews(self, feedback_service):
        rates = await feedback_service.compute_agreement_rate()
        assert rates["agreement_rate"] == 0.0
        assert rates["total_reviewed"] == 0
