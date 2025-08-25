from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "model_version" in j
