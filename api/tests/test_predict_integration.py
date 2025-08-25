from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)

def test_predict_smoke():
    r = client.post("/predict", json={"text": "You are awesome!"})
    assert r.status_code == 200
    j = r.json()
    assert set(["id","label","probability","model_version"]).issubset(j.keys())
