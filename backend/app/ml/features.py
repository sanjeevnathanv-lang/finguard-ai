"""Feature engineering service for financial transaction risk intelligence.
Strictly guarantees anti-leakage boundary enforcement and currency separation.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import math
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.ml.schemas import FeatureVectorSchema

FEATURE_SCHEMA_VERSION = "1.0.0"

# Ordered numerical feature names for machine learning vectors
FEATURE_NAMES: List[str] = [
    "amount",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_night",
    "has_sender",
    "has_receiver",
    "has_notes",
    "sender_txn_count_1h",
    "sender_txn_count_24h",
    "sender_txn_count_7d",
    "seconds_since_prev_txn_log",
    "amount_to_mean_ratio",
    "amount_to_max_ratio",
    "amount_zscore",
    # One-hot encoded channels
    "channel_ONLINE",
    "channel_MOBILE_APP",
    "channel_ATM",
    "channel_POS",
    "channel_BRANCH",
    # One-hot encoded transaction types
    "type_PAYMENT",
    "type_TRANSFER",
    "type_PURCHASE",
    "type_WITHDRAWAL",
]


class FeatureExtractor:
    """Extracts testable, deterministic feature vectors from persisted transaction records."""

    def __init__(self, schema_version: str = FEATURE_SCHEMA_VERSION):
        self.schema_version = schema_version

    @staticmethod
    def _normalize_utc(dt: datetime) -> datetime:
        """Ensure datetime has UTC timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def extract_features(
        self,
        transaction: Transaction,
        db: Optional[Session] = None,
    ) -> FeatureVectorSchema:
        """
        Extract complete feature representation for a transaction record.
        Enforces strict temporal anti-leakage: never includes future records.
        """
        txn_ts = self._normalize_utc(transaction.timestamp)
        amount_float = float(transaction.amount)
        curr = (transaction.currency or "INR").upper()

        # 1. Direct temporal features
        hour = txn_ts.hour
        day_of_week = txn_ts.weekday()
        is_weekend = 1 if day_of_week in (5, 6) else 0
        is_night = 1 if 0 <= hour <= 5 else 0

        # 2. Direct data-quality / missingness indicators
        has_sender = 1 if (transaction.sender_reference and transaction.sender_reference.strip()) else 0
        has_receiver = 1 if (transaction.receiver_reference and transaction.receiver_reference.strip()) else 0
        has_notes = 1 if (transaction.notes and transaction.notes.strip()) else 0

        # 3. Default historical metrics (when no database history is available)
        count_1h = 1
        count_24h = 1
        count_7d = 1
        seconds_since_prev: Optional[float] = None
        hist_mean: Optional[float] = None
        hist_max: Optional[float] = None
        hist_std: Optional[float] = None
        amount_to_mean_ratio = 1.0
        amount_to_max_ratio = 1.0
        amount_zscore = 0.0

        # 4. Historical behavioral extraction with strict anti-leakage filtering
        if db is not None and has_sender:
            sender = transaction.sender_reference.strip()

            # Anti-leakage condition: strictly prior in time, or identical timestamp with lower ID
            temporal_filter = or_(
                Transaction.timestamp < transaction.timestamp,
                and_(
                    Transaction.timestamp == transaction.timestamp,
                    Transaction.id < (transaction.id or 0),
                )
            )

            # A. Window count queries (All currencies from this sender in temporal window)
            one_hour_prior = txn_ts - timedelta(hours=1)
            past_1h_count = (
                db.query(func.count(Transaction.id))
                .filter(
                    Transaction.sender_reference == sender,
                    temporal_filter,
                    Transaction.timestamp >= one_hour_prior,
                )
                .scalar() or 0
            )
            count_1h = past_1h_count + 1

            one_day_prior = txn_ts - timedelta(days=1)
            past_24h_count = (
                db.query(func.count(Transaction.id))
                .filter(
                    Transaction.sender_reference == sender,
                    temporal_filter,
                    Transaction.timestamp >= one_day_prior,
                )
                .scalar() or 0
            )
            count_24h = past_24h_count + 1

            seven_days_prior = txn_ts - timedelta(days=7)
            past_7d_count = (
                db.query(func.count(Transaction.id))
                .filter(
                    Transaction.sender_reference == sender,
                    temporal_filter,
                    Transaction.timestamp >= seven_days_prior,
                )
                .scalar() or 0
            )
            count_7d = past_7d_count + 1

            # B. Time since previous transaction from same sender
            prev_txn = (
                db.query(Transaction)
                .filter(
                    Transaction.sender_reference == sender,
                    temporal_filter,
                )
                .order_by(Transaction.timestamp.desc(), Transaction.id.desc())
                .first()
            )
            if prev_txn is not None:
                prev_ts = self._normalize_utc(prev_txn.timestamp)
                diff = (txn_ts - prev_ts).total_seconds()
                seconds_since_prev = max(0.0, float(diff))

            # C. Historical Amount Statistics (Strictly within compatible currency)
            prior_amounts_query = (
                db.query(Transaction.amount)
                .filter(
                    Transaction.sender_reference == sender,
                    Transaction.currency == curr,
                    temporal_filter,
                )
                .all()
            )

            if prior_amounts_query:
                amounts = [float(row[0]) for row in prior_amounts_query]
                hist_mean = float(np.mean(amounts))
                hist_max = float(np.max(amounts))
                hist_std = float(np.std(amounts)) if len(amounts) > 1 else 0.0

                if hist_mean > 0.0:
                    amount_to_mean_ratio = float(round(amount_float / hist_mean, 4))
                if hist_max > 0.0:
                    amount_to_max_ratio = float(round(amount_float / hist_max, 4))
                if hist_std > 0.0:
                    amount_zscore = float(round((amount_float - hist_mean) / hist_std, 4))

        return FeatureVectorSchema(
            feature_schema_version=self.schema_version,
            transaction_id=transaction.id,
            transaction_reference=transaction.reference,
            timestamp=txn_ts,
            currency=curr,
            amount=amount_float,
            hour_of_day=hour,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            is_night=is_night,
            channel=(transaction.channel or "UNKNOWN").upper(),
            transaction_type=(transaction.transaction_type or "PAYMENT").upper(),
            has_sender=has_sender,
            has_receiver=has_receiver,
            has_notes=has_notes,
            sender_txn_count_1h=count_1h,
            sender_txn_count_24h=count_24h,
            sender_txn_count_7d=count_7d,
            seconds_since_prev_txn=seconds_since_prev,
            sender_hist_amount_mean=hist_mean,
            sender_hist_amount_max=hist_max,
            sender_hist_amount_std=hist_std,
            amount_to_mean_ratio=amount_to_mean_ratio,
            amount_to_max_ratio=amount_to_max_ratio,
            amount_zscore=amount_zscore,
        )

    def vectorize(self, features: FeatureVectorSchema) -> np.ndarray:
        """
        Convert a FeatureVectorSchema into a fixed-length numerical vector for ML models.
        Applies robust log transformation to unbounded variables (amounts, delays).
        """
        # Log scale for amount (prevents extreme outlier distortion)
        log_amount = math.log1p(max(0.0, features.amount))

        # Log scale for seconds since previous transaction
        if features.seconds_since_prev_txn is not None:
            log_sec_prev = math.log1p(max(0.0, features.seconds_since_prev_txn))
        else:
            log_sec_prev = 15.0  # Sentinel representation for first observed transaction (~10 days)

        # One-hot encoding for channel
        ch = features.channel.upper()
        ch_online = 1.0 if ch == "ONLINE" else 0.0
        ch_mobile = 1.0 if ch == "MOBILE_APP" else 0.0
        ch_atm = 1.0 if ch == "ATM" else 0.0
        ch_pos = 1.0 if ch == "POS" else 0.0
        ch_branch = 1.0 if ch == "BRANCH" else 0.0

        # One-hot encoding for transaction type
        tt = features.transaction_type.upper()
        tt_payment = 1.0 if tt == "PAYMENT" else 0.0
        tt_transfer = 1.0 if tt == "TRANSFER" else 0.0
        tt_purchase = 1.0 if tt == "PURCHASE" else 0.0
        tt_withdrawal = 1.0 if tt == "WITHDRAWAL" else 0.0

        vec = [
            log_amount,
            float(features.hour_of_day),
            float(features.day_of_week),
            float(features.is_weekend),
            float(features.is_night),
            float(features.has_sender),
            float(features.has_receiver),
            float(features.has_notes),
            float(features.sender_txn_count_1h),
            float(features.sender_txn_count_24h),
            float(features.sender_txn_count_7d),
            log_sec_prev,
            float(min(50.0, features.amount_to_mean_ratio)),
            float(min(50.0, features.amount_to_max_ratio)),
            float(max(-10.0, min(10.0, features.amount_zscore))),
            ch_online,
            ch_mobile,
            ch_atm,
            ch_pos,
            ch_branch,
            tt_payment,
            tt_transfer,
            tt_purchase,
            tt_withdrawal,
        ]

        return np.array(vec, dtype=np.float64)

    def batch_extract_and_vectorize(
        self,
        transactions: List[Transaction],
        db: Optional[Session] = None,
    ) -> Tuple[np.ndarray, List[FeatureVectorSchema]]:
        """Batch extract features in chronological order, returning numeric matrix and schemas."""
        # Ensure input transactions are sorted chronologically
        sorted_txns = sorted(transactions, key=lambda t: (t.timestamp, t.id or 0))
        schemas: List[FeatureVectorSchema] = []
        vectors: List[np.ndarray] = []

        for txn in sorted_txns:
            feat = self.extract_features(txn, db=db)
            schemas.append(feat)
            vectors.append(self.vectorize(feat))

        matrix = np.array(vectors, dtype=np.float64) if vectors else np.empty((0, len(FEATURE_NAMES)))
        return matrix, schemas
