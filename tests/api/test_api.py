"""Tests for the FastAPI sentiment API."""
# flake8: noqa: E402

# --- path shim so 'from api.main import app' works in all runners ---
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------------------

from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    # Accept either form
    assert data.get("status") in {"ok", "healthy"}


def test_predict_positive_example():
    r = client.post("/predict", json={"text": "I love this product!"})
    assert r.status_code == 200
    data = r.json()
    assert "sentiment" in data
    assert data["sentiment"] in {"positive", "neutral", "negative"}


def test_predict_negative_example():
    r = client.post("/predict", json={"text": "This is awful."})
    assert r.status_code == 200
    data = r.json()
    assert "sentiment" in data
    assert data["sentiment"] in {"positive", "neutral", "negative"}


def test_predict_missing_text():
    r = client.post("/predict", json={})
    assert r.status_code in (400, 422)


def test_predict_malformed_type():
    r = client.post("/predict", json={"text": 123})
    assert r.status_code in (400, 422)
