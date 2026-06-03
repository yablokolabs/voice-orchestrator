"""Integration tests for the FastAPI application."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from voice_orchestrator.api.app import create_app
from voice_orchestrator.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(tmp_path) -> TestClient:
    import os
    os.environ["VO_UPLOAD_DIR"] = str(tmp_path / "uploads")
    os.environ["VO_ENVIRONMENT"] = "test"
    os.environ["VO_DEBUG"] = "true"
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as c:
        yield c
    # Clean up env vars
    for key in ("VO_UPLOAD_DIR", "VO_ENVIRONMENT", "VO_DEBUG"):
        os.environ.pop(key, None)
    get_settings.cache_clear()


class TestHealth:
    def test_health_returns_200_with_healthy_status(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"


class TestAudioUpload:
    def test_upload_valid_file_returns_200(self, client: TestClient):
        audio_bytes = b"RIFF" + b"\x00" * 100
        resp = client.post(
            "/api/v1/audio/upload",
            files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "audio_file_id" in body
        assert body["filename"] == "test.wav"

    def test_upload_invalid_format_returns_400(self, client: TestClient):
        resp = client.post(
            "/api/v1/audio/upload",
            files={"file": ("test.xyz", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_oversized_file_returns_400(self, client: TestClient):
        # Default max is 50 MB; our test settings use default
        big_data = b"\x00" * (51 * 1024 * 1024)
        resp = client.post(
            "/api/v1/audio/upload",
            files={"file": ("big.wav", io.BytesIO(big_data), "audio/wav")},
        )
        assert resp.status_code == 400


class TestMetrics:
    def test_get_metrics_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200


class TestExtractActions:
    def test_no_text_or_audio_returns_400(self, client: TestClient):
        resp = client.post("/api/v1/extract-actions", json={})
        assert resp.status_code == 400
        assert "text" in resp.json()["detail"].lower() or "audio_file_id" in resp.json()["detail"]
