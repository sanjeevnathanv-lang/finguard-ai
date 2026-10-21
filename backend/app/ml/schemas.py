"""Pydantic schemas for Phase 4 Feature Engineering, Model Readiness,
Anomaly Detection, Supervised Training, and Hybrid Assessment Orchestration.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FeatureVectorSchema(BaseModel):
    """Normalized, typed feature vector extracted from a transaction."""
    feature_schema_version: str = "1.0.0"
    transaction_id: Optional[int] = None
    transaction_reference: str
    timestamp: datetime
    currency: str

    # Direct Transaction Features
    amount: float = Field(..., description="Normalized transaction amount")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of transaction in UTC")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    is_weekend: int = Field(..., description="Binary indicator: 1 if Saturday or Sunday, else 0")
    is_night: int = Field(..., description="Binary indicator: 1 if between 00:00 and 05:59 UTC, else 0")
    channel: str = Field(..., description="Transaction channel (ONLINE, MOBILE_APP, etc.)")
    transaction_type: str = Field(..., description="Transaction classification")

    # Data Quality & Missingness Indicators
    has_sender: int = Field(..., description="1 if sender reference is populated, else 0")
    has_receiver: int = Field(..., description="1 if receiver reference is populated, else 0")
    has_notes: int = Field(..., description="1 if transaction context notes are populated, else 0")

    # Historical Sender Behavioral Features (Strictly Anti-Leakage & Currency-Compatible)
    sender_txn_count_1h: int = Field(default=1, description="Past transactions by sender in 1-hour window (including current)")
    sender_txn_count_24h: int = Field(default=1, description="Past transactions by sender in 24-hour window (including current)")
    sender_txn_count_7d: int = Field(default=1, description="Past transactions by sender in 7-day window (including current)")
    seconds_since_prev_txn: Optional[float] = Field(default=None, description="Seconds since immediate previous transaction from sender (-1.0 if first seen)")

    # Historical Currency-Compatible Monetary Statistics
    sender_hist_amount_mean: Optional[float] = Field(default=None, description="Mean past transaction amount for this sender in same currency")
    sender_hist_amount_max: Optional[float] = Field(default=None, description="Max past transaction amount for this sender in same currency")
    sender_hist_amount_std: Optional[float] = Field(default=None, description="Standard deviation of past amounts for this sender in same currency")
    amount_to_mean_ratio: float = Field(default=1.0, description="Ratio of current amount to historical sender mean (1.0 if no prior history)")
    amount_to_max_ratio: float = Field(default=1.0, description="Ratio of current amount to historical sender max (1.0 if no prior history)")
    amount_zscore: float = Field(default=0.0, description="Standardized deviation from historical sender mean (0.0 if insufficient variance)")


class AnomalyInferenceResult(BaseModel):
    """Unsupervised anomaly detection findings."""
    model_name: str
    model_version: str
    model_type: str = "UNSUPERVISED_ANOMALY_DETECTION"
    is_anomaly: bool = Field(..., description="True if transaction exhibits outlier characteristics beyond contamination threshold")
    anomaly_score: float = Field(..., description="Continuous anomaly magnitude (higher means more atypical)")
    anomaly_signal: str = Field(..., description="Categorical signal: NORMAL, ELEVATED_ANOMALY, HIGH_ANOMALY")
    top_feature_contributions: Dict[str, float] = Field(default_factory=dict, description="Key features contributing to the anomaly assessment")
    evaluation_basis: str = Field(
        default="Empirical feature divergence from historical transaction distribution",
        description="Methodological basis for the anomaly signal"
    )
    disclaimer: str = Field(
        default="This is an unsupervised statistical anomaly signal, NOT a verified fraud probability or confirmed fraud determination.",
        description="Mandatory academic and operational disclaimer"
    )


class ModelReadinessReport(BaseModel):
    """Structured report documenting model availability and ground-truth label requirements."""
    supervised_model_status: str = Field(..., description="Status: UNAVAILABLE_MISSING_LABELS | TRAINED | INSUFFICIENT_DATA")
    unsupervised_model_status: str = Field(..., description="Status: AVAILABLE | INSUFFICIENT_TRANSACTIONS | UNTRAINED")
    active_unsupervised_model: Optional[str] = None
    unsupervised_model_version: Optional[str] = None
    total_persisted_transactions: int
    minimum_transactions_for_anomaly_model: int = 10
    supervised_label_requirements: Dict[str, Any] = Field(
        default_factory=lambda: {
            "required_label_field": "is_fraud (binary integer 0 or 1)",
            "label_definition": "Independently confirmed fraudulent outcome verified by chargeback, card network alert, or completed investigation.",
            "lifecycle_status_warning": "Transaction lifecycle status ('COMPLETED', 'PENDING', 'FLAGGED', 'FAILED') represents settlement state, NOT a ground-truth fraud outcome.",
            "minimum_positive_cases_required": 10,
            "minimum_total_labelled_cases_required": 30,
        }
    )
    feature_schema_version: str = "1.0.0"
    features_registered: List[str]


class ModelEvaluationMetrics(BaseModel):
    """Empirical evaluation metrics for a trained supervised or unsupervised model."""
    model_id: str
    model_version: str
    algorithm: str
    trained_at: datetime
    is_supervised: bool
    status: str
    dataset_fingerprint: str
    training_sample_count: int
    evaluation_sample_count: int
    metrics: Dict[str, Any] = Field(default_factory=dict)
    confusion_matrix: Optional[List[List[int]]] = None
    limitations: List[str] = Field(default_factory=list)


class TrainModelRequest(BaseModel):
    """Payload to trigger a supervised model training run."""
    algorithm: str = Field(default="LOGISTIC_REGRESSION", description="LOGISTIC_REGRESSION or DECISION_TREE")
    test_size: float = Field(default=0.25, ge=0.1, le=0.5, description="Fraction of records held out for evaluation")
    time_aware_split: bool = Field(default=True, description="Enforce strict chronological train/test split to prevent temporal leakage")
    class_weight: str = Field(default="balanced", description="Class weighting strategy for handling imbalanced distributions")


class HybridAssessmentReport(BaseModel):
    """Synthesized decision-support report combining Rule Engine and Model Findings."""
    assessment_id: Optional[int] = None
    transaction_id: Optional[int] = None
    transaction_reference: str
    timestamp: datetime
    orchestrator_version: str = "1.0.0"
    knowledge_base_version: str
    feature_schema_version: str = "1.0.0"

    # Component A: Rule-Based Expert System (Phase 3)
    rule_engine: Dict[str, Any]

    # Component B: Machine Learning / Anomaly Intelligence (Phase 4)
    ml_intelligence: Optional[AnomalyInferenceResult] = None
    ml_status: str

    # Component C: Feature Snapshot
    feature_vector: FeatureVectorSchema

    # Component D: Hybrid Synthesis & Comparison
    synthesis_verdict: str
    synthesis_severity: str
    concordance_analysis: str
    recommendation_rationale: str
    investigation_priority: str
    academic_disclaimer: str = (
        "FinGuard AI is an academic prototype for risk analysis and investigation support. "
        "It does NOT execute automated transaction cancellation or make definitive fraud determinations."
    )


class TransactionPatternAnalytics(BaseModel):
    """Persisted transaction pattern intelligence."""
    total_analyzed_transactions: int
    query_timestamp: datetime
    currency_distribution: Dict[str, int]
    channel_distribution: Dict[str, int]
    transaction_type_distribution: Dict[str, int]
    hourly_distribution: Dict[int, int]
    day_of_week_distribution: Dict[int, int]
    top_active_senders: List[Dict[str, Any]]
    average_amounts_by_currency: Dict[str, float]
    max_amounts_by_currency: Dict[str, float]
