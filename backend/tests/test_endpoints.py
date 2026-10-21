from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_dashboard_metrics():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "flagged_transactions" in data
    assert "status_distribution" in data
    assert "volume_by_currency" in data
    assert data["system_health"] == "ok"
