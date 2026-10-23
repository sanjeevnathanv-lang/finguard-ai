"""Dashboard API routes.
Provides live metric data aggregated directly from the persisted database records.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.deps import require_analyst
from app.schemas.transaction import DashboardMetricsResponse
from app.services import transaction_service

router = APIRouter()

@router.get("/dashboard", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Return aggregated metrics derived from the database."""
    try:
        return transaction_service.get_dashboard_metrics(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate dashboard metrics: {str(e)}"
        )


@router.post("/dashboard/reset-metrics")
def reset_dashboard_metrics(
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Purge all transaction history and operational surveillance data, resetting dashboard metrics."""
    try:
        result = transaction_service.reset_transactions_and_data(
            db=db,
            actor_username=current_user.username,
            actor_role=current_user.role,
        )
        fresh_metrics = transaction_service.get_dashboard_metrics(db)
        return {
            **result,
            "metrics": fresh_metrics,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics and clear transactions: {str(e)}",
        )

