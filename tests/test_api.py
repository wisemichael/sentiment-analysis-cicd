import os
os.environ["TESTING"] = "1"  # avoid DB in tests

from fastapi.testclient import TestClient
from api.app.main import app

def test_health_ok():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_predict_happy_path():
    c = TestClient(app)
    r = c.post("/predict", json={"text": "you are nice"})
    assert r.status_code == 200
    data = r.json()
    assert {"id","label","probability","model_version"} <= set(data.keys())
