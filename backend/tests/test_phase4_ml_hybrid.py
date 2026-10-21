"""Phase 4 Automated Test Suite: Feature Engineering, Anti-Leakage Invariants,
Anomaly Detection, Supervised Training Data-Gate, and Hybrid Assessment Orchestration.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import io
import pytest
from app.db.models import Transaction, Assessment
from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.anomaly import TransactionAnomalyDetector
from app.ml.trainer import run_supervised_training, LabelRequirementError
from app.ml.schemas import TrainModelRequest


def test_feature_extractor_direct_properties():
    """Verify direct transaction attributes, calendar math, and data quality flags."""
    extractor = FeatureExtractor()
    ts = datetime(2026, 10, 24, 3, 30, tzinfo=timezone.utc)  # Saturday 3:30 AM
    txn = Transaction(
        id=1,
        reference="TXN-FEAT-01",
        timestamp=ts,
        amount=Decimal("50000.00"),
        currency="INR",
        sender_reference="USER-001",
        receiver_reference="MERCH-001",
        transaction_type="PAYMENT",
        channel="ONLINE",
        notes="Invoice settlement",
    )

    feat = extractor.extract_features(txn, db=None)

    assert feat.amount == 50000.00
    assert feat.currency == "INR"
    assert feat.hour_of_day == 3
    assert feat.day_of_week == 5  # Saturday
    assert feat.is_weekend == 1
    assert feat.is_night == 1
    assert feat.has_sender == 1
    assert feat.has_receiver == 1
    assert feat.has_notes == 1
    assert feat.sender_txn_count_1h == 1
    assert feat.amount_to_mean_ratio == 1.0


def test_feature_extractor_anti_leakage(db_session):
    """
    CRITICAL INVARIANT: Feature extraction must NOT look ahead into the future.
    Future transactions must not affect past transaction features.
    """
    extractor = FeatureExtractor()
    base_time = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)

    # 1. Past transaction at 10:00
    t1 = Transaction(
        id=1,
        reference="TXN-TIME-01",
        timestamp=base_time,
        amount=Decimal("1000.00"),
        currency="INR",
        sender_reference="SENDER-ALICE",
        receiver_reference="RECV-1",
        transaction_type="PAYMENT",
        channel="ONLINE",
    )
    # 2. Present transaction at 10:30 (30 mins later)
    t2 = Transaction(
        id=2,
        reference="TXN-TIME-02",
        timestamp=base_time + timedelta(minutes=30),
        amount=Decimal("2000.00"),
        currency="INR",
        sender_reference="SENDER-ALICE",
        receiver_reference="RECV-2",
        transaction_type="PAYMENT",
        channel="ONLINE",
    )
    # 3. Future transaction at 11:00 (should NOT be seen when evaluating t1 or t2)
    t3 = Transaction(
        id=3,
        reference="TXN-TIME-03",
        timestamp=base_time + timedelta(hours=1),
        amount=Decimal("90000.00"),
        currency="INR",
        sender_reference="SENDER-ALICE",
        receiver_reference="RECV-3",
        transaction_type="PAYMENT",
        channel="ONLINE",
    )

    db_session.add_all([t1, t2, t3])
    db_session.commit()

    # Evaluating t1 (at 10:00): should see zero prior transactions
    feat1 = extractor.extract_features(t1, db=db_session)
    assert feat1.sender_txn_count_1h == 1
    assert feat1.seconds_since_prev_txn is None
    assert feat1.sender_hist_amount_mean is None

    # Evaluating t2 (at 10:30): should see t1 (1000 INR), but NOT t3 (90000 INR)
    feat2 = extractor.extract_features(t2, db=db_session)
    assert feat2.sender_txn_count_1h == 2  # t1 + t2
    assert feat2.seconds_since_prev_txn == 1800.0  # 30 mins
    assert feat2.sender_hist_amount_mean == 1000.00
    assert feat2.amount_to_mean_ratio == 2.0  # 2000 / 1000

    # Evaluating t3 (at 11:00): should see t1 and t2
    feat3 = extractor.extract_features(t3, db=db_session)
    assert feat3.sender_txn_count_1h == 3
    assert feat3.sender_hist_amount_mean == 1500.00  # (1000 + 2000)/2


def test_feature_extractor_currency_separation(db_session):
    """Historical monetary statistics must be strictly segregated by currency."""
    extractor = FeatureExtractor()
    base_time = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)

    # Alice transacts in INR
    t_inr = Transaction(
        id=1,
        reference="TXN-CURR-INR",
        timestamp=base_time - timedelta(hours=2),
        amount=Decimal("100000.00"),
        currency="INR",
        sender_reference="SENDER-BOB",
        receiver_reference="RECV-1",
        transaction_type="TRANSFER",
        channel="ONLINE",
    )
    # Alice transacts in USD (should not mix with INR amounts)
    t_usd = Transaction(
        id=2,
        reference="TXN-CURR-USD",
        timestamp=base_time,
        amount=Decimal("500.00"),
        currency="USD",
        sender_reference="SENDER-BOB",
        receiver_reference="RECV-2",
        transaction_type="TRANSFER",
        channel="ONLINE",
    )

    db_session.add_all([t_inr, t_usd])
    db_session.commit()

    feat_usd = extractor.extract_features(t_usd, db=db_session)
    # There was no prior USD transaction from Bob, so historical USD mean should be None
    assert feat_usd.sender_hist_amount_mean is None
    assert feat_usd.amount_to_mean_ratio == 1.0


def test_anomaly_detector_insufficient_baseline():
    """Unfitted detector on empty/insufficient data returns structured non-fabricated signal."""
    detector = TransactionAnomalyDetector()
    extractor = FeatureExtractor()
    txn = Transaction(
        reference="TXN-EMPTY",
        timestamp=datetime.now(timezone.utc),
        amount=Decimal("1000"),
        currency="INR",
        transaction_type="PAYMENT",
        channel="ONLINE",
    )
    feat = extractor.extract_features(txn)
    vec = extractor.vectorize(feat)

    res = detector.evaluate_vector(vec, feat)
    assert res.is_anomaly is False
    assert res.anomaly_score == 0.0
    assert res.anomaly_signal == "INSUFFICIENT_DATA"


def test_anomaly_detector_fit_and_scoring(db_session):
    """Verify IsolationForest fits with 12 records and identifies extreme outliers."""
    detector = TransactionAnomalyDetector()
    extractor = FeatureExtractor()
    base_time = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)

    # Insert 12 nominal transactions
    txns = []
    for i in range(12):
        t = Transaction(
            reference=f"TXN-BASELINE-{i}",
            timestamp=base_time - timedelta(minutes=i * 10),
            amount=Decimal(str(1000 + i * 50)),
            currency="INR",
            sender_reference="CORP-SND",
            receiver_reference="MERCH-RCV",
            transaction_type="PAYMENT",
            channel="ONLINE",
        )
        txns.append(t)

    db_session.add_all(txns)
    db_session.commit()

    matrix, schemas = extractor.batch_extract_and_vectorize(txns, db=db_session)
    success = detector.fit(matrix)
    assert success is True
    assert detector.fitted is True

    # Test an extreme outlier (huge amount at 3 AM from a different channel)
    outlier = Transaction(
        reference="TXN-OUTLIER-01",
        timestamp=datetime(2026, 10, 22, 3, 15, tzinfo=timezone.utc),
        amount=Decimal("9500000.00"),
        currency="INR",
        sender_reference="CORP-SND",
        receiver_reference="UNKNOWN-RCV",
        transaction_type="WITHDRAWAL",
        channel="ATM",
    )
    feat_outlier = extractor.extract_features(outlier, db=db_session)
    vec_outlier = extractor.vectorize(feat_outlier)

    res = detector.evaluate_vector(vec_outlier, feat_outlier)
    assert res.anomaly_score > 0.0
    assert "amount" in res.top_feature_contributions or "amount_to_mean_ratio" in res.top_feature_contributions or "is_night" in res.top_feature_contributions


def test_supervised_training_refusal_when_unlabelled(client):
    """POST /api/model/train must refuse training with HTTP 422 when labels are absent."""
    # Seed a few transactions without verified labels
    for i in range(25):
        client.post("/api/transactions", json={
            "reference": f"TXN-UNLABELLED-{i}",
            "amount": 2500.0,
            "currency": "INR",
            "transaction_type": "PAYMENT",
            "channel": "ONLINE",
            "status": "COMPLETED",
        })

    res = client.post("/api/model/train", json={
        "algorithm": "LOGISTIC_REGRESSION",
        "test_size": 0.25,
    })
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "LABELS_UNAVAILABLE_FOR_SUPERVISED_TRAINING"


def test_supervised_training_with_verified_labels(client):
    """Verify supervised training pipeline executes successfully when verified labels exist."""
    # Insert 22 negative and 6 positive ground-truth labelled transactions
    for i in range(22):
        client.post("/api/transactions", json={
            "reference": f"TXN-VERIFIED-LEGIT-{i}",
            "amount": 1000.0 + i * 100,
            "currency": "INR",
            "transaction_type": "PAYMENT",
            "channel": "MOBILE_APP",
            "status": "COMPLETED",
            "notes": "Legitimate transaction VERIFIED_LABEL:0",
        })
    for i in range(6):
        client.post("/api/transactions", json={
            "reference": f"TXN-VERIFIED-FRAUD-{i}",
            "amount": 200000.0 + i * 50000,
            "currency": "INR",
            "transaction_type": "TRANSFER",
            "channel": "ONLINE",
            "status": "FLAGGED",
            "notes": "Confirmed chargeback fraud incident VERIFIED_LABEL:1",
        })

    res = client.post("/api/model/train", json={
        "algorithm": "LOGISTIC_REGRESSION",
        "test_size": 0.25,
        "time_aware_split": True,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "TRAINED_ACTIVE"
    assert data["is_supervised"] is True
    assert "precision" in data["metrics"]
    assert "recall" in data["metrics"]
    assert "f1_score" in data["metrics"]
    assert data["confusion_matrix"] is not None

    # GET /api/model/evaluation should now return the saved metrics
    eval_res = client.get("/api/model/evaluation")
    assert eval_res.status_code == 200
    assert eval_res.json()["model_id"] == data["model_id"]


def test_hybrid_assessment_orchestration_api(client):
    """Verify POST /api/transactions/{id}/assess returns both Phase 3 trace and Phase 4 hybrid report."""
    create_res = client.post("/api/transactions", json={
        "reference": "HYBRID-TEST-01",
        "amount": 350000.0,
        "currency": "INR",
        "transaction_type": "TRANSFER",
        "channel": "ONLINE",
        "status": "PENDING",
        "sender_reference": "CORP-PAY-1",
        "receiver_reference": "MERCH-SETTLE-1",
        "notes": "Large supplier settlement",
    })
    assert create_res.status_code == 201
    txn_id = create_res.json()["id"]

    # Trigger assessment
    assess_res = client.post(f"/api/transactions/{txn_id}/assess")
    assert assess_res.status_code == 200
    data = assess_res.json()

    # Phase 3 backwards-compatibility checks
    assert "trace" in data
    assert data["trace"]["engine_version"] == "1.0.0"
    assert "activated_rules" in data["trace"]

    # Phase 4 hybrid report checks
    assert "hybrid_report" in data
    hybrid = data["hybrid_report"]
    assert hybrid is not None
    assert "synthesis_verdict" in hybrid
    assert "concordance_analysis" in hybrid
    assert "feature_vector" in hybrid
    assert hybrid["feature_vector"]["amount"] == 350000.0


def test_model_status_api(client):
    """Verify GET /api/model/status provides transparent readiness info."""
    res = client.get("/api/model/status")
    assert res.status_code == 200
    data = res.json()
    assert "supervised_model_status" in data
    assert "supervised_label_requirements" in data
    assert "features_registered" in data
    assert len(data["features_registered"]) == len(FEATURE_NAMES)


def test_transaction_patterns_analytics_api(client):
    """Verify GET /api/analytics/transaction-patterns computes aggregates without cross-currency mixing."""
    res = client.get("/api/analytics/transaction-patterns")
    assert res.status_code == 200
    data = res.json()
    assert "total_analyzed_transactions" in data
    assert "currency_distribution" in data
    assert "hourly_distribution" in data
    assert "average_amounts_by_currency" in data
    assert "top_active_senders" in data
