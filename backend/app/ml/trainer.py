"""Supervised machine-learning training pipeline.
Strictly data-gated: refuses training when ground-truth binary labels are missing or degenerate.
"""

from datetime import datetime, timezone
import hashlib
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.schemas import (
    ModelEvaluationMetrics,
    TrainModelRequest,
)

MIN_LABELLED_SAMPLES = 20
MIN_POSITIVE_SAMPLES = 5


class LabelRequirementError(Exception):
    """Raised when supervised training is requested on unlabelled or invalid data."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def extract_ground_truth_labels(transactions: List[Transaction]) -> Tuple[List[int], List[Transaction]]:
    """
    Inspect transaction records for independently verified ground-truth fraud labels.
    Strictly adheres to banking compliance standards:
    - Transaction 'status' (COMPLETED, PENDING, FLAGGED, FAILED) is NEVER treated as a fraud label.
    - Ground-truth is only established if an explicit verified disposition is recorded in 'notes'
      (e.g., 'VERIFIED_LABEL:1' / 'VERIFIED_LABEL:0' or 'CHARGEBACK_CONFIRMED').
    """
    labelled_txns: List[Transaction] = []
    labels: List[int] = []

    for txn in transactions:
        note = (txn.notes or "").upper()
        if "VERIFIED_LABEL:1" in note or "CHARGEBACK_CONFIRMED" in note:
            labels.append(1)
            labelled_txns.append(txn)
        elif "VERIFIED_LABEL:0" in note or "VERIFIED_LEGITIMATE" in note:
            labels.append(0)
            labelled_txns.append(txn)

    return labels, labelled_txns


def run_supervised_training(
    db: Session,
    request: TrainModelRequest,
    extractor: Optional[FeatureExtractor] = None,
) -> ModelEvaluationMetrics:
    """
    Train a reproducible supervised classifier on verified ground-truth data.
    Refuses execution if ground truth labels are absent, insufficient, or single-class.
    """
    feature_extractor = extractor or FeatureExtractor()

    # 1. Fetch all transactions chronologically
    all_txns = db.query(Transaction).order_by(Transaction.timestamp.asc(), Transaction.id.asc()).all()

    if len(all_txns) < MIN_LABELLED_SAMPLES:
        raise LabelRequirementError(
            message=f"Insufficient total transactions for supervised training. Have {len(all_txns)}, require at least {MIN_LABELLED_SAMPLES}.",
            details={
                "current_count": len(all_txns),
                "required_count": MIN_LABELLED_SAMPLES,
            }
        )

    # 2. Extract ground truth labels
    labels, labelled_txns = extract_ground_truth_labels(all_txns)

    if len(labels) < MIN_LABELLED_SAMPLES:
        raise LabelRequirementError(
            message=(
                f"Missing ground-truth fraud labels. Only {len(labels)} of {len(all_txns)} records have verified disposition labels. "
                f"Supervised model training strictly requires at least {MIN_LABELLED_SAMPLES} verified ground-truth cases. "
                "Notice: Transaction lifecycle status ('COMPLETED', 'PENDING', 'FLAGGED', 'FAILED') represents operational settlement state, NOT confirmed fraud."
            ),
            details={
                "labelled_count": len(labels),
                "total_transactions": len(all_txns),
                "required_minimum": MIN_LABELLED_SAMPLES,
                "label_spec": "Verified disposition must be recorded via 'VERIFIED_LABEL:1' or 'VERIFIED_LABEL:0'.",
            }
        )

    pos_count = sum(labels)
    neg_count = len(labels) - pos_count

    if pos_count < MIN_POSITIVE_SAMPLES or neg_count < MIN_POSITIVE_SAMPLES:
        raise LabelRequirementError(
            message=(
                f"Degenerate class distribution. Found {pos_count} positive and {neg_count} negative labels. "
                f"Requires at least {MIN_POSITIVE_SAMPLES} samples per class to evaluate generalization."
            ),
            details={
                "positive_cases": pos_count,
                "negative_cases": neg_count,
                "minimum_per_class": MIN_POSITIVE_SAMPLES,
            }
        )

    # 3. Vectorize labelled transactions
    X, _ = feature_extractor.batch_extract_and_vectorize(labelled_txns, db=db)
    y = np.array(labels, dtype=np.int32)

    # 4. Train/Test Split
    from sklearn.model_selection import train_test_split
    if request.time_aware_split:
        split_idx = int(len(X) * (1.0 - request.test_size))
        # Ensure both classes exist in train and test partitions
        if len(np.unique(y[:split_idx])) < 2 or len(np.unique(y[split_idx:])) < 2:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=request.test_size, stratify=y, random_state=42
            )
            split_strategy = "STRATIFIED_SPLIT (chronological split had one class concentrated in single window)"
        else:
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            split_strategy = "TIME_AWARE_CHRONOLOGICAL"
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=request.test_size, stratify=y, random_state=42
        )
        split_strategy = "STRATIFIED_SPLIT"

    # Check that test set contains both classes for metric computation
    test_has_both_classes = len(np.unique(y_test)) > 1

    # 5. Fit Algorithm
    algo_name = request.algorithm.upper()
    if algo_name == "DECISION_TREE":
        clf = DecisionTreeClassifier(
            max_depth=5,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
        )
    else:
        algo_name = "LOGISTIC_REGRESSION"
        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )

    clf.fit(X_train, y_train)

    # 6. Evaluate on Held-Out Test Set
    y_pred = clf.predict(X_test)
    cm = confusion_matrix(y_test, y_pred).tolist()

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None

    if test_has_both_classes and hasattr(clf, "predict_proba"):
        probs = clf.predict_proba(X_test)[:, 1]
        try:
            roc_auc = float(round(roc_auc_score(y_test, probs), 4))
            pr_auc = float(round(average_precision_score(y_test, probs), 4))
        except Exception:
            pass

    # Dataset Fingerprint
    fingerprint_raw = f"{len(labelled_txns)}-{pos_count}-{neg_count}-{X.shape[1]}"
    fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()[:12]

    metrics = {
        "split_strategy": split_strategy,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "positive_train_samples": int(sum(y_train)),
        "positive_test_samples": int(sum(y_test)),
    }

    limitations = [
        "Model trained on historical disposition labels; past fraud distributions may shift over time.",
        "Class imbalance handled via inverse-frequency weighting; performance sensitive to false positive volume.",
        "Must be reviewed by human investigators in conjunction with deterministic expert system rules.",
    ]

    return ModelEvaluationMetrics(
        model_id=f"finguard-{algo_name.lower()}-v1",
        model_version="1.0.0",
        algorithm=algo_name,
        trained_at=datetime.now(timezone.utc),
        is_supervised=True,
        status="TRAINED_ACTIVE",
        dataset_fingerprint=fingerprint,
        training_sample_count=len(X_train),
        evaluation_sample_count=len(X_test),
        metrics=metrics,
        confusion_matrix=cm,
        limitations=limitations,
    )
