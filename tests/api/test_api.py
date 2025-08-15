import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_predict_endpoint():
    response = client.post("/predict", json={"text": "This is great!"})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data

