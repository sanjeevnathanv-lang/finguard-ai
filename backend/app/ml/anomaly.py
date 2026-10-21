"""Unsupervised transaction anomaly detection engine.
Provides statistically grounded outlier scoring using scikit-learn IsolationForest
without fabricating calibrated fraud probabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
import math
import numpy as np
from sklearn.ensemble import IsolationForest

from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.schemas import FeatureVectorSchema, AnomalyInferenceResult

ANOMALY_MODEL_VERSION = "1.0.0"
MIN_TRANSACTIONS_FOR_FIT = 10


class TransactionAnomalyDetector:
    """Unsupervised Isolation Forest anomaly detector with feature contribution explanation."""

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        version: str = ANOMALY_MODEL_VERSION,
    ):
        self.version = version
        self.contamination = contamination
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.fitted: bool = False
        self.training_sample_count: int = 0
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None

    def fit(self, feature_matrix: np.ndarray) -> bool:
        """
        Fit IsolationForest on an extracted numerical feature matrix.
        Requires at least MIN_TRANSACTIONS_FOR_FIT samples to establish baseline.
        """
        if feature_matrix.shape[0] < MIN_TRANSACTIONS_FOR_FIT:
            self.fitted = False
            return False

        # Compute empirical baseline statistics for feature deviation attribution
        self.feature_means = np.mean(feature_matrix, axis=0)
        stds = np.std(feature_matrix, axis=0)
        # Prevent division by zero on static features
        self.feature_stds = np.where(stds == 0.0, 1.0, stds)

        # Fit IsolationForest
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )
        self.model.fit(feature_matrix)
        self.fitted = True
        self.training_sample_count = int(feature_matrix.shape[0])
        return True

    def evaluate_vector(
        self,
        vector: np.ndarray,
        features: FeatureVectorSchema,
    ) -> AnomalyInferenceResult:
        """
        Evaluate a single numerical feature vector and produce an AnomalyInferenceResult.
        """
        if not self.fitted or self.model is None:
            # Fallback when model has not been trained on sufficient baseline data
            return AnomalyInferenceResult(
                model_name="IsolationForest (Unfitted)",
                model_version=self.version,
                model_type="UNSUPERVISED_ANOMALY_DETECTION",
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_signal="INSUFFICIENT_DATA",
                top_feature_contributions={},
                evaluation_basis="Baseline unestablished; requires minimum 10 historical records for empirical fit.",
            )

        # Reshape to 2D array for sklearn
        vec_2d = vector.reshape(1, -1)

        # decision_function: lower means more abnormal (negative for outliers)
        raw_score = float(self.model.decision_function(vec_2d)[0])
        pred = int(self.model.predict(vec_2d)[0])  # -1 for anomaly, +1 for normal

        # Normalize score into a human-interpretable [0.0, 1.0] anomaly magnitude
        # Typical decision_function values range from -0.3 to +0.3
        # We map via logistic sigmoid centered at 0: higher = more anomalous
        normalized_score = float(round(1.0 / (1.0 + math.exp(raw_score * 8.0)), 4))

        is_anomaly = bool(pred == -1)

        if normalized_score >= 0.70 or is_anomaly:
            signal = "HIGH_ANOMALY"
        elif normalized_score >= 0.45:
            signal = "ELEVATED_ANOMALY"
        else:
            signal = "NORMAL"

        # Calculate feature deviation contributions against baseline
        contributions: Dict[str, float] = {}
        if self.feature_means is not None and self.feature_stds is not None:
            deviations = np.abs((vector - self.feature_means) / self.feature_stds)
            # Find top 3 most deviating features
            top_indices = np.argsort(deviations)[-3:][::-1]
            for idx in top_indices:
                feat_name = FEATURE_NAMES[idx]
                dev_val = float(round(deviations[idx], 2))
                if dev_val > 0.5:
                    contributions[feat_name] = dev_val

        return AnomalyInferenceResult(
            model_name="IsolationForest",
            model_version=self.version,
            model_type="UNSUPERVISED_ANOMALY_DETECTION",
            is_anomaly=is_anomaly,
            anomaly_score=normalized_score,
            anomaly_signal=signal,
            top_feature_contributions=contributions,
            evaluation_basis=f"Isolation Forest multi-tree partitioning over {self.training_sample_count} baseline records.",
        )
