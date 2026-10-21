"""API routes for Machine Learning Models, Readiness Reports, and Training.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.deps import require_analyst, require_viewer
from app.services.audit_service import record_audit_event
from app.ml.registry import default_model_registry
from app.ml.trainer import run_supervised_training, LabelRequirementError
from app.ml.schemas import (
    ModelReadinessReport,
    ModelEvaluationMetrics,
    TrainModelRequest,
)

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/status", response_model=ModelReadinessReport)
def get_model_status(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """
    Return comprehensive ML model status and readiness report.
    Explains ground-truth label requirements and unsupervised anomaly detection baseline.
    """
    return default_model_registry.get_readiness_report(db)


@router.get("/evaluation", response_model=ModelEvaluationMetrics)
def get_model_evaluation(
    current_user: User = Depends(require_viewer),
):
    """
    Return empirical held-out evaluation metrics for the active supervised model.
    Returns HTTP 404 if no supervised model has been trained.
    """
    evaluation = default_model_registry.get_model_evaluation()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No trained supervised model evaluation available. "
                "Supervised training is data-gated and requires verified ground-truth disposition labels."
            ),
        )
    return evaluation


@router.post("/train", response_model=ModelEvaluationMetrics)
def train_supervised_model_endpoint(
    request: TrainModelRequest,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """
    Data-gated supervised model training pipeline.
    Strictly verifies existence of ground-truth binary labels before fitting.
    Refuses execution with HTTP 422 Unprocessable Entity if ground-truth labels are absent or degenerate.
    """
    try:
        metrics = run_supervised_training(db, request)
        default_model_registry.latest_supervised_evaluation = metrics
        record_audit_event(
            db,
            event_type="MODEL_SUPERVISED_TRAINED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            status="SUCCESS",
            metadata={"algorithm": request.algorithm, "test_size": request.test_size},
        )
        return metrics
    except LabelRequirementError as e:
        record_audit_event(
            db,
            event_type="MODEL_TRAINING_REFUSED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            status="FAILURE",
            metadata={"reason": e.message},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "LABELS_UNAVAILABLE_FOR_SUPERVISED_TRAINING",
                "message": e.message,
                "details": e.details,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training pipeline failure: {str(e)}",
        )
