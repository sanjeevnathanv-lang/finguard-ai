from fastapi.testclient import TestClient
from app.main import app
from app.db.models import Transaction, AuditLog, User

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_dashboard_metrics(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "flagged_transactions" in data
    assert "status_distribution" in data
    assert "volume_by_currency" in data
    assert data["system_health"] == "ok"


def test_reset_metrics_unauthorized(unauthenticated_client):
    """Anonymous/unauthenticated requests must be rejected."""
    res = unauthenticated_client.post("/api/dashboard/reset-metrics")
    assert res.status_code == 401


def test_reset_metrics_viewer_forbidden(viewer_client):
    """Viewers must be forbidden from clearing transaction data."""
    res = viewer_client.post("/api/dashboard/reset-metrics")
    assert res.status_code == 403


def test_reset_metrics_clears_data_and_resets_dashboard(client, db_session):
    """Analysts can successfully reset metrics, purging transactions while preserving users & audit logs."""
    # 1. Create a test transaction
    client.post(
        "/api/transactions",
        json={
            "reference": "TXN-RESET-001",
            "amount": 50000.0,
            "currency": "INR",
            "sender_reference": "ACC-RESET-1",
            "receiver_reference": "ACC-RESET-2",
            "transaction_type": "TRANSFER",
            "channel": "MOBILE_APP",
            "status": "COMPLETED",
        },
    )

    # 2. Verify dashboard shows 1 transaction
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    assert res.json()["total_transactions"] == 1

    # 3. Trigger reset metrics
    reset_res = client.post("/api/dashboard/reset-metrics")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "cleared"
    assert reset_data["transactions_deleted"] >= 1
    assert reset_data["metrics"]["total_transactions"] == 0

    # 4. Verify dashboard now returns 0 transactions
    after_res = client.get("/api/dashboard")
    assert after_res.status_code == 200
    assert after_res.json()["total_transactions"] == 0
    assert len(after_res.json()["volume_by_currency"]) == 0

    # 5. Verify database transactions table is empty
    assert db_session.query(Transaction).count() == 0

    # 6. Verify audit log captured the TRANSACTIONS_PURGED event
    purge_log = (
        db_session.query(AuditLog)
        .filter(AuditLog.event_type == "TRANSACTIONS_PURGED")
        .first()
    )
    assert purge_log is not None
    assert purge_log.status == "SUCCESS"


def test_transactions_reset_endpoint(client, db_session):
    """POST /api/transactions/reset works identically."""
    client.post(
        "/api/transactions",
        json={
            "reference": "TXN-RESET-002",
            "amount": 1000.0,
            "currency": "USD",
            "sender_reference": "ACC-RESET-3",
            "receiver_reference": "ACC-RESET-4",
            "transaction_type": "PAYMENT",
            "channel": "ONLINE",
            "status": "COMPLETED",
        },
    )
    assert db_session.query(Transaction).count() == 1

    res = client.post("/api/transactions/reset")
    assert res.status_code == 200
    assert res.json()["status"] == "cleared"
    assert res.json()["transactions_deleted"] == 1
    assert db_session.query(Transaction).count() == 0

