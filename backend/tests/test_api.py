"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.app import app
    return TestClient(app)


class TestSystemAPI:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Local AI Voice Studio"

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_system_info(self, client):
        response = client.get("/api/system")
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "ram" in data
        assert "gpu" in data
        assert "cuda" in data
        assert "recommended_device" in data
        assert "recommended_models" in data


class TestModelsAPI:
    def test_list_models(self, client):
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 4

    def test_get_model(self, client):
        response = client.get("/api/models/chatterbox-multilingual-v3")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "chatterbox-multilingual-v3"

    def test_get_model_not_found(self, client):
        response = client.get("/api/models/nonexistent")
        assert response.status_code == 404


class TestVoicesAPI:
    def test_list_voices(self, client):
        response = client.get("/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "count" in data


class TestHistoryAPI:
    def test_list_history(self, client):
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data

    def test_history_stats(self, client):
        response = client.get("/api/history/stats")
        assert response.status_code == 200
        data = response.json()
        assert "generated_count" in data
        assert "total_duration_seconds" in data


class TestTTSAPI:
    def test_generate_missing_text(self, client):
        response = client.post("/api/tts", json={
            "text": "",
            "language": "en",
        })
        assert response.status_code == 422  # Validation error

    def test_generate_invalid_language(self, client):
        response = client.post("/api/tts", json={
            "text": "Hello world",
            "language": "xx",
        })
        assert response.status_code == 422
