import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ai.schemas import AssessmentResponse, InferenceTraceDTO
from app.services import assessment_service
from app.services.assessment_service import (
    TransactionNotFoundError,
    AssessmentNotFoundError,
)
from app.core.deps import require_analyst, require_viewer
from app.db.models import User
from app.services.audit_service import record_audit_event

router = APIRouter(tags=["assessments"])

def format_assessment_response(assessment) -> AssessmentResponse:
    trace_dict = json.loads(assessment.trace_json)
    hybrid_dict = None
    if getattr(assessment, "hybrid_report_json", None):
        try:
            hybrid_dict = json.loads(assessment.hybrid_report_json)
        except Exception:
            hybrid_dict = None

    return AssessmentResponse(
        assessment_id=assessment.id,
        transaction_id=assessment.transaction_id,
        transaction_reference=assessment.transaction_reference,
        final_recommendation=assessment.final_recommendation,
        overall_severity=assessment.overall_severity,
        risk_score=float(assessment.risk_score),
        rules_triggered_count=assessment.rules_triggered_count,
        created_at=assessment.created_at,
        trace=InferenceTraceDTO(**trace_dict),
        hybrid_report=hybrid_dict,
        model_version=getattr(assessment, "model_version", None),
    )


@router.post("/transactions/{transaction_id}/assess", response_model=AssessmentResponse)
def assess_transaction_endpoint(
    transaction_id: int,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """
    Execute forward-chaining rule evaluation on a stored transaction.
    Records derived facts, triggered rules, conflict resolutions, and audit snapshot.
    """
    try:
        assessment = assessment_service.assess_transaction(db, transaction_id)
        record_audit_event(
            db,
            event_type="ASSESSMENT_PERFORMED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=assessment.transaction_reference,
            status="SUCCESS",
            metadata={
                "assessment_id": assessment.id,
                "recommendation": assessment.final_recommendation,
                "risk_score": float(assessment.risk_score),
            },
        )
        return format_assessment_response(assessment)
    except TransactionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Expert assessment failed: {str(e)}",
        )


@router.get("/transactions/{transaction_id}/assessments", response_model=List[AssessmentResponse])
def get_transaction_assessments_endpoint(
    transaction_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve full assessment history for a specific transaction."""
    assessments = assessment_service.get_assessments_for_transaction(db, transaction_id)
    return [format_assessment_response(a) for a in assessments]


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment_endpoint(
    assessment_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve an assessment by ID with complete explainable trace."""
    try:
        assessment = assessment_service.get_assessment(db, assessment_id)
        return format_assessment_response(assessment)
    except AssessmentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
