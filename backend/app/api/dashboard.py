"""Dashboard API routes.
Provides live metric data aggregated directly from the persisted database records.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
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
