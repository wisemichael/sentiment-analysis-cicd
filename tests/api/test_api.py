# tests/api/test_api.py
from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


def test_predict_positive():
    r = client.post("/predict", json={"text": "I love this product!"})
    assert r.status_code == 200
    data = r.json()
    assert data["sentiment"] in {"positive", "neutral", "negative"}


def test_predict_negative_example():
    r = client.post("/predict", json={"text": "This is awful."})
    assert r.status_code == 200
    assert r.json()["sentiment"] in {"positive", "neutral", "negative"}


def test_predict_missing_text():
    r = client.post("/predict", json={})
    assert r.status_code in (400, 422)


def test_predict_malformed_type():
    r = client.post("/predict", json={"text": 123})
    assert r.status_code in (400, 422)

