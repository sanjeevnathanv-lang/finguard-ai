"""Hybrid Risk Assessment Orchestration Service.
Orchestrates:
1. Feature extraction with historical behavioral context and anti-leakage protection.
2. Rule-based expert system inference (Phase 3 forward chaining).
3. Machine-learning anomaly detection (Phase 4 Isolation Forest).
4. Transparent evidence synthesis contrasting rule findings with statistical signals.
"""

from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.db.models import Transaction, Assessment
from app.ai.facts import FactSet
from app.ai.knowledge_base import KnowledgeBase
from app.ai.inference_engine import ForwardChainingEngine
from app.services.fact_extractor import extract_facts_from_transaction
from app.ml.features import FeatureExtractor
from app.ml.registry import ModelRegistry, default_model_registry
from app.ml.schemas import (
    HybridAssessmentReport,
    AnomalyInferenceResult,
    FeatureVectorSchema,
)

ORCHESTRATOR_VERSION = "1.0.0"


class HybridOrchestrator:
    """Combines deterministic expert rules with empirical machine-learning signals."""

    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        model_registry: Optional[ModelRegistry] = None,
        feature_extractor: Optional[FeatureExtractor] = None,
    ):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.engine = ForwardChainingEngine(self.knowledge_base)
        self.model_registry = model_registry or default_model_registry
        self.feature_extractor = feature_extractor or FeatureExtractor()

    def orchestrate_assessment(
        self,
        transaction: Transaction,
        db: Session,
    ) -> Tuple[Assessment, HybridAssessmentReport]:
        """
        Execute full multi-paradigm hybrid assessment:
        1. Extract domain facts and numerical feature vector.
        2. Run forward chaining expert rules engine.
        3. Run unsupervised anomaly detector.
        4. Synthesize transparent concordance / divergence analysis.
        5. Persist immutable assessment snapshot.
        """
        now = datetime.now(timezone.utc)

        # 1. Feature Vector Extraction
        feature_vector = self.feature_extractor.extract_features(transaction, db=db)

        # 2. Expert Rule Inference (Phase 3)
        fact_set = extract_facts_from_transaction(transaction, db=db)
        rule_trace = self.engine.run_inference(fact_set)

        # 3. Machine Learning Anomaly Inference (Phase 4)
        ml_result: Optional[AnomalyInferenceResult] = None
        ml_status = "EVALUATED"

        try:
            ml_result = self.model_registry.evaluate_transaction_anomaly(transaction, db=db)
            if ml_result.anomaly_signal == "INSUFFICIENT_DATA":
                ml_status = "UNAVAILABLE_INSUFFICIENT_BASELINE"
        except Exception as e:
            ml_status = f"EVALUATION_ERROR: {str(e)}"
            ml_result = None

        # 4. Hybrid Synthesis & Concordance Analysis
        rule_rec = rule_trace.final_recommendation
        rule_sev = rule_trace.overall_severity

        # Determine Concordance between Rule Engine and ML Anomaly Detector
        is_ml_anomalous = bool(ml_result and ml_result.is_anomaly)
        ml_signal = ml_result.anomaly_signal if ml_result else "UNKNOWN"

        concordance_analysis = ""
        synthesis_verdict = rule_rec
        synthesis_severity = rule_sev

        if rule_rec in ("HUMAN_SUPERVISORY_REVIEW", "EXPEDITED_SECURITY_INTERVENTION"):
            if is_ml_anomalous or ml_signal in ("HIGH_ANOMALY", "ELEVATED_ANOMALY"):
                concordance_analysis = (
                    "CONCORDANT_HIGH_RISK: Both the deterministic rule engine and the empirical anomaly detector "
                    "flagged this transaction. Rule conditions matched known risk patterns and Isolation Forest "
                    f"detected significant empirical feature divergence (Anomaly Score: {ml_result.anomaly_score if ml_result else 'N/A'})."
                )
                investigation_priority = "URGENT_PRIORITY_1"
            else:
                concordance_analysis = (
                    "RULE_DRIVEN_EVALUATION: The rule engine identified specific domain policy triggers, while the "
                    "statistical anomaly model found the feature geometry relatively close to nominal distributions. "
                    "The rule recommendation takes precedence."
                )
                investigation_priority = "HIGH_PRIORITY_2"
        else:
            # Rule recommendation is STANDARD_PROCESSING
            if is_ml_anomalous or ml_signal == "HIGH_ANOMALY":
                concordance_analysis = (
                    "DIVERGENT_ANOMALY_ALERT: Deterministic rules satisfied routine criteria, BUT the unsupervised "
                    f"anomaly detector identified unusual multi-dimensional divergence (Anomaly Score: {ml_result.anomaly_score if ml_result else 'N/A'}). "
                    "Supervisory spot-check recommended to verify novel behavioral shifts."
                )
                synthesis_verdict = "SUPERVISORY_SPOT_CHECK"
                synthesis_severity = "MEDIUM"
                investigation_priority = "MEDIUM_PRIORITY_3"
            else:
                concordance_analysis = (
                    "CONCORDANT_ROUTINE: Both systems agree. No deterministic risk rules were triggered and "
                    "statistical features reside within nominal baseline bounds."
                )
                investigation_priority = "ROUTINE_PRIORITY_4"

        recommendation_rationale = (
            f"Rule Engine Output: {rule_rec} ({rule_sev}). "
            f"ML Anomaly Signal: {ml_signal} (Score: {ml_result.anomaly_score if ml_result else 'N/A'}). "
            f"Summary: {concordance_analysis}"
        )

        # 5. Build Structured Hybrid Report
        hybrid_report = HybridAssessmentReport(
            transaction_id=transaction.id,
            transaction_reference=transaction.reference,
            timestamp=now,
            orchestrator_version=ORCHESTRATOR_VERSION,
            knowledge_base_version=self.knowledge_base.version,
            feature_schema_version=self.feature_extractor.schema_version,
            rule_engine={
                "recommendation": rule_rec,
                "severity": rule_sev,
                "risk_score": rule_trace.risk_score,
                "activated_rules_count": len(rule_trace.activated_rules),
                "activated_rules": [r.model_dump() for r in rule_trace.activated_rules],
                "untriggered_rule_ids": rule_trace.untriggered_rule_ids,
                "conflicts_detected": [c.model_dump() for c in rule_trace.conflicts_detected],
                "human_readable_summary": rule_trace.human_readable_summary,
            },
            ml_intelligence=ml_result,
            ml_status=ml_status,
            feature_vector=feature_vector,
            synthesis_verdict=synthesis_verdict,
            synthesis_severity=synthesis_severity,
            concordance_analysis=concordance_analysis,
            recommendation_rationale=recommendation_rationale,
            investigation_priority=investigation_priority,
        )

        # 6. Transactional Persistence to Assessment DB Model
        assessment = Assessment(
            transaction_id=transaction.id,
            transaction_reference=transaction.reference,
            final_recommendation=synthesis_verdict,
            overall_severity=synthesis_severity,
            risk_score=rule_trace.risk_score,
            rules_triggered_count=len(rule_trace.activated_rules),
            engine_version=rule_trace.engine_version,
            knowledge_base_version=self.knowledge_base.version,
            model_version=ml_result.model_version if ml_result else None,
            trace_json=rule_trace.model_dump_json(),
            hybrid_report_json=hybrid_report.model_dump_json(),
            created_at=now,
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # Set the persisted id onto the report
        hybrid_report.assessment_id = assessment.id

        return assessment, hybrid_report
