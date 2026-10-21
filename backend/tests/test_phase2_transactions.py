import io
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest
from app.db.models import Transaction
from app.services.transaction_service import create_transaction
from app.schemas.transaction import TransactionCreate

def test_empty_database_dashboard(client):
    """Dashboard handles empty database cleanly without errors."""
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 0
    assert data["system_health"] == "ok"
    assert data["status_distribution"]["COMPLETED"] == 0
    assert len(data["volume_by_currency"]) == 0
    assert data["latest_transaction_timestamp"] is None

def test_create_valid_transaction(client):
    """Create a single valid transaction successfully."""
    payload = {
        "reference": "TXN-TEST-1001",
        "amount": 2500.75,
        "currency": "INR",
        "sender_reference": "USER-123",
        "receiver_reference": "MERCH-456",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
        "status": "COMPLETED",
        "notes": "Test payment note"
    }
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["reference"] == "TXN-TEST-1001"
    assert float(data["amount"]) == 2500.75
    assert data["currency"] == "INR"
    assert data["id"] is not None
    assert data["dataset_provenance"] == "MANUAL_ENTRY"
    assert data["is_synthetic"] is False

def test_create_transaction_duplicate_reference(client):
    """Reject duplicate transaction reference with HTTP 409 Conflict."""
    payload = {
        "reference": "TXN-DUP-01",
        "amount": 100.0,
        "currency": "INR",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
    }
    res1 = client.post("/api/transactions", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/transactions", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_create_transaction_invalid_inputs(client):
    """Reject negative, zero, or invalid amounts, invalid currency, and invalid types with HTTP 422."""
    # Negative amount
    res_neg = client.post("/api/transactions", json={
        "amount": -50.0,
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
    })
    assert res_neg.status_code == 422

    # Zero amount
    res_zero = client.post("/api/transactions", json={
        "amount": 0.0,
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
    })
    assert res_zero.status_code == 422

    # Invalid currency
    res_curr = client.post("/api/transactions", json={
        "amount": 100.0,
        "currency": "XYZ",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
    })
    assert res_curr.status_code == 422

    # Invalid channel
    res_chan = client.post("/api/transactions", json={
        "amount": 100.0,
        "channel": "TELEPATHY",
        "transaction_type": "PAYMENT",
    })
    assert res_chan.status_code == 422

def test_get_transaction_by_id(client):
    """Retrieve transaction by ID, returning 404 if not found."""
    # 404 for missing ID
    res_missing = client.get("/api/transactions/999999")
    assert res_missing.status_code == 404

    # Create then retrieve
    create_res = client.post("/api/transactions", json={
        "reference": "TXN-FIND-01",
        "amount": 750.0,
        "currency": "INR",
        "transaction_type": "TRANSFER",
        "channel": "MOBILE_APP",
    })
    txn_id = create_res.json()["id"]

    res_found = client.get(f"/api/transactions/{txn_id}")
    assert res_found.status_code == 200
    assert res_found.json()["reference"] == "TXN-FIND-01"

def test_pagination_and_filtering(client):
    """Verify paginated listing, search filtering, and stable ordering."""
    # Insert 15 transactions
    for i in range(1, 16):
        client.post("/api/transactions", json={
            "reference": f"TXN-FILTER-{i:03d}",
            "amount": float(i * 100),
            "currency": "INR" if i % 2 == 0 else "USD",
            "transaction_type": "PAYMENT" if i <= 10 else "WITHDRAWAL",
            "channel": "ONLINE" if i % 3 == 0 else "ATM",
            "status": "COMPLETED" if i <= 12 else "FLAGGED",
            "sender_reference": f"USER-{i}",
        })

    # Page 1 with page_size=5
    res_p1 = client.get("/api/transactions?page=1&page_size=5")
    assert res_p1.status_code == 200
    p1_data = res_p1.json()
    assert len(p1_data["items"]) == 5
    assert p1_data["total"] == 15
    assert p1_data["total_pages"] == 3

    # Filter by currency=USD
    res_usd = client.get("/api/transactions?currency=USD")
    assert res_usd.status_code == 200
    usd_data = res_usd.json()
    assert all(item["currency"] == "USD" for item in usd_data["items"])
    assert usd_data["total"] == 8

    # Filter by status=FLAGGED
    res_flagged = client.get("/api/transactions?status=FLAGGED")
    assert res_flagged.status_code == 200
    assert res_flagged.json()["total"] == 3

    # Search term
    res_search = client.get("/api/transactions?search=FILTER-007")
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["reference"] == "TXN-FILTER-007"

    # Sorting by amount asc
    res_sort = client.get("/api/transactions?sort_by=amount&sort_order=asc&page_size=3")
    assert res_sort.status_code == 200
    items = res_sort.json()["items"]
    assert float(items[0]["amount"]) <= float(items[1]["amount"]) <= float(items[2]["amount"])

def test_csv_upload_valid_file(client):
    """Ingest transactions from a valid CSV file."""
    csv_content = (
        "reference,timestamp,amount,currency,sender_reference,receiver_reference,transaction_type,channel,status\n"
        "CSV-001,2026-10-21 10:00:00,1200.50,INR,SND-1,RCV-1,PAYMENT,ONLINE,COMPLETED\n"
        "CSV-002,2026-10-21 10:05:00,450.00,USD,SND-2,RCV-2,TRANSFER,MOBILE_APP,COMPLETED\n"
        "CSV-003,2026-10-21 10:10:00,8900.00,INR,SND-3,RCV-3,PURCHASE,POS,COMPLETED\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/api/transactions/upload",
        files={"file": ("transactions.csv", file_obj, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 3
    assert data["imported_rows"] == 3
    assert data["rejected_rows"] == 0
    assert len(data["errors"]) == 0

    # Verify they appear in database
    chk = client.get("/api/transactions?search=CSV-001")
    assert chk.json()["total"] == 1
    assert chk.json()["items"][0]["dataset_provenance"].startswith("CSV_IMPORT:")

def test_csv_upload_validation_errors(client):
    """Identify row-level errors in malformed CSV without crashing."""
    csv_content = (
        "reference,amount,currency,transaction_type,channel\n"
        "ERR-01,-500.00,INR,PAYMENT,ONLINE\n"           # negative amount
        "ERR-02,abc,INR,PAYMENT,ONLINE\n"               # non-numeric amount
        "ERR-03,150.00,INVALID,PAYMENT,ONLINE\n"        # invalid currency
        "ERR-04,200.00,INR,UNKNOWN_TYPE,ONLINE\n"       # invalid type
        "ERR-05,300.00,INR,PAYMENT,ONLINE\n"            # valid row
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/api/transactions/upload",
        files={"file": ("errors.csv", file_obj, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 5
    assert data["imported_rows"] == 1  # only ERR-05
    assert data["rejected_rows"] == 4
    assert len(data["errors"]) == 4

def test_csv_upload_duplicate_references(client):
    """Handle duplicates within CSV and against database."""
    # Pre-create in DB
    client.post("/api/transactions", json={
        "reference": "EXISTING-REF-01",
        "amount": 300.0,
        "currency": "INR",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
    })

    csv_content = (
        "reference,amount,currency,transaction_type,channel\n"
        "EXISTING-REF-01,500.00,INR,PAYMENT,ONLINE\n"   # duplicate against DB
        "DUP-IN-FILE,100.00,INR,PAYMENT,ONLINE\n"        # first occurrence
        "DUP-IN-FILE,200.00,INR,PAYMENT,ONLINE\n"        # duplicate within file
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/api/transactions/upload",
        files={"file": ("duplicates.csv", file_obj, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported_rows"] == 1  # only first DUP-IN-FILE succeeds
    assert data["rejected_rows"] == 2

def test_csv_upload_empty_and_missing_headers(client):
    """Reject empty CSV or files missing required headers with HTTP 400."""
    # Empty file
    res_empty = client.post(
        "/api/transactions/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    )
    assert res_empty.status_code == 400

    # Missing required header ('amount' missing)
    bad_header_csv = io.BytesIO(b"reference,currency,channel\nTXN-1,INR,ONLINE\n")
    res_missing_col = client.post(
        "/api/transactions/upload",
        files={"file": ("bad_header.csv", bad_header_csv, "text/csv")}
    )
    assert res_missing_col.status_code == 400
    assert "Missing required columns" in res_missing_col.json()["detail"]

def test_dashboard_metrics_aggregation(client):
    """Verify metrics calculation strictly groups volume by currency and status."""
    client.post("/api/transactions", json={
        "reference": "DASH-INR-1",
        "amount": 1000.0,
        "currency": "INR",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
        "status": "COMPLETED",
    })
    client.post("/api/transactions", json={
        "reference": "DASH-INR-2",
        "amount": 2500.0,
        "currency": "INR",
        "transaction_type": "TRANSFER",
        "channel": "MOBILE_APP",
        "status": "COMPLETED",
    })
    client.post("/api/transactions", json={
        "reference": "DASH-USD-1",
        "amount": 50.0,
        "currency": "USD",
        "transaction_type": "PAYMENT",
        "channel": "ONLINE",
        "status": "FLAGGED",
    })

    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["total_transactions"] == 3
    assert data["status_distribution"]["COMPLETED"] == 2
    assert data["status_distribution"]["FLAGGED"] == 1
    # Check volume is separated by currency
    assert data["volume_by_currency"]["INR"] == 3500.0
    assert data["volume_by_currency"]["USD"] == 50.0

def test_realtime_transaction_ingestion_and_provenance(client):
    """Verify realtime transaction ingestion guarantees authentic provenance and is_synthetic=False."""
    # Ingest a direct real-time transaction
    res = client.post("/api/transactions", json={
        "reference": "REALTIME-LIVE-01",
        "amount": 7500.0,
        "currency": "INR",
        "transaction_type": "PAYMENT",
        "channel": "MOBILE_APP",
        "status": "COMPLETED",
        "sender_reference": "USR-LIVE-1",
        "receiver_reference": "MERCH-LIVE-1",
    })
    assert res.status_code == 201
    created = res.json()
    assert created["is_synthetic"] is False
    assert created["dataset_provenance"] == "MANUAL_ENTRY"

    # Query transaction listing and ensure only real-time records are returned
    chk = client.get("/api/transactions?search=REALTIME-LIVE-01")
    assert chk.status_code == 200
    items = chk.json()["items"]
    assert len(items) == 1
    assert items[0]["is_synthetic"] is False
    assert items[0]["dataset_provenance"] == "MANUAL_ENTRY"
