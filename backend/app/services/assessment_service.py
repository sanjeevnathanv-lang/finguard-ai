import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Transaction, Assessment
from app.ai.facts import FactSet, Fact, FactSource
from app.ai.knowledge_base import KnowledgeBase
from app.ai.inference_engine import ForwardChainingEngine
from app.ai.explanation import InferenceTrace
from app.services.fact_extractor import extract_facts_from_transaction
from app.services.hybrid_service import HybridOrchestrator

# Global shared knowledge base and orchestrator instances
default_knowledge_base = KnowledgeBase()
default_engine = ForwardChainingEngine(default_knowledge_base)
default_orchestrator = HybridOrchestrator(default_knowledge_base)

class TransactionNotFoundError(Exception):
    def __init__(self, transaction_id: int):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction with ID {transaction_id} does not exist.")


class AssessmentNotFoundError(Exception):
    def __init__(self, assessment_id: int):
        self.assessment_id = assessment_id
        super().__init__(f"Assessment with ID {assessment_id} does not exist.")


def assess_transaction(
    db: Session,
    transaction_id: int,
    engine: Optional[ForwardChainingEngine] = None,
) -> Assessment:
    """
    Execute full hybrid evaluation (Expert Rules + Feature Intelligence + ML Anomaly Detection)
    for a transaction in the database.
    """
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise TransactionNotFoundError(transaction_id)

    orchestrator = (
        HybridOrchestrator(knowledge_base=engine.knowledge_base)
        if engine
        else default_orchestrator
    )

    assessment, _ = orchestrator.orchestrate_assessment(txn, db=db)
    return assessment


def evaluate_custom_facts(
    facts_input: List[dict],
    engine: Optional[ForwardChainingEngine] = None,
) -> InferenceTrace:
    """Evaluate an arbitrary validated fact set (useful for unit testing and interactive rule tuning)."""
    inference_engine = engine or default_engine
    fact_set = FactSet()

    for item in facts_input:
        val = item["value"]
        fact_set.add_fact(Fact(
            name=item["name"],
            value=val,
            source=FactSource.USER_INPUT,
            description=item.get("description", ""),
        ))

    return inference_engine.run_inference(fact_set)


def get_assessment(db: Session, assessment_id: int) -> Assessment:
    """Retrieve stored assessment by ID."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise AssessmentNotFoundError(assessment_id)
    return assessment


def get_assessments_for_transaction(db: Session, transaction_id: int) -> List[Assessment]:
    """Retrieve history of assessments for a specific transaction."""
    return (
        db.query(Assessment)
        .filter(Assessment.transaction_id == transaction_id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .all()
    )
