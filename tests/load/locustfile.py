"""Locust load test for the Voice Orchestrator API."""

from __future__ import annotations

import io

from locust import HttpUser, between, task


class VoiceOrchestratorUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(2)
    def get_metrics(self):
        self.client.get("/api/v1/metrics")

    @task(1)
    def upload_audio(self):
        audio_bytes = b"RIFF" + b"\x00" * 100
        self.client.post(
            "/api/v1/audio/upload",
            files={"file": ("load_test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        )
