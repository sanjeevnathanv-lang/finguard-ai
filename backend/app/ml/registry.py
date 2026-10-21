"""Model Registry & Readiness Evaluation Subsystem.
Tracks machine-learning model availability, empirical baselines, and evaluation artifacts.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.anomaly import TransactionAnomalyDetector, MIN_TRANSACTIONS_FOR_FIT
from app.ml.schemas import (
    ModelReadinessReport,
    ModelEvaluationMetrics,
    AnomalyInferenceResult,
)
from app.ml.trainer import extract_ground_truth_labels

REGISTRY_VERSION = "1.0.0"


class ModelRegistry:
    """Central registry for unsupervised and supervised machine learning components."""

    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.anomaly_detector = TransactionAnomalyDetector()
        self.latest_supervised_evaluation: Optional[ModelEvaluationMetrics] = None

    def refresh_unsupervised_baseline(self, db: Session) -> bool:
        """
        Check database records and fit or refresh the IsolationForest baseline
        if sufficient transaction records exist.
        """
        txns = db.query(Transaction).all()
        if len(txns) < MIN_TRANSACTIONS_FOR_FIT:
            return False

        # Extract features and fit IsolationForest
        matrix, _ = self.feature_extractor.batch_extract_and_vectorize(txns, db=db)
        return self.anomaly_detector.fit(matrix)

    def evaluate_transaction_anomaly(
        self,
        transaction: Transaction,
        db: Optional[Session] = None,
    ) -> AnomalyInferenceResult:
        """
        Extract features and evaluate unsupervised anomaly metrics for a transaction.
        """
        # If not fitted and db is provided, try fitting baseline first
        if not self.anomaly_detector.fitted and db is not None:
            self.refresh_unsupervised_baseline(db)

        features = self.feature_extractor.extract_features(transaction, db=db)
        vector = self.feature_extractor.vectorize(features)
        return self.anomaly_detector.evaluate_vector(vector, features)

    def get_readiness_report(self, db: Session) -> ModelReadinessReport:
        """
        Compile an honest status report regarding ML model readiness,
        ground-truth label absence, and anomaly model baseline.
        """
        total_txns = db.query(Transaction).count()
        labels, labelled_txns = extract_ground_truth_labels(db.query(Transaction).all())

        if len(labels) >= 20:
            supervised_status = "READY_FOR_TRAINING"
            if self.latest_supervised_evaluation:
                supervised_status = "TRAINED_ACTIVE"
        else:
            supervised_status = "UNAVAILABLE_MISSING_LABELS"

        unsupervised_status = (
            "AVAILABLE" if (self.anomaly_detector.fitted or total_txns >= MIN_TRANSACTIONS_FOR_FIT)
            else "INSUFFICIENT_TRANSACTIONS"
        )

        return ModelReadinessReport(
            supervised_model_status=supervised_status,
            unsupervised_model_status=unsupervised_status,
            active_unsupervised_model="IsolationForest" if unsupervised_status == "AVAILABLE" else None,
            unsupervised_model_version=self.anomaly_detector.version if unsupervised_status == "AVAILABLE" else None,
            total_persisted_transactions=total_txns,
            minimum_transactions_for_anomaly_model=MIN_TRANSACTIONS_FOR_FIT,
            feature_schema_version=self.feature_extractor.schema_version,
            features_registered=FEATURE_NAMES,
        )

    def get_model_evaluation(self) -> Optional[ModelEvaluationMetrics]:
        """Return genuine evaluation metrics for active supervised model, if trained."""
        return self.latest_supervised_evaluation


# Shared global instance
default_model_registry = ModelRegistry()
