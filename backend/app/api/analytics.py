"""API routes for Persisted Transaction Pattern Analytics.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml.schemas import TransactionPatternAnalytics
from app.services.analytics_service import compute_transaction_patterns

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/transaction-patterns", response_model=TransactionPatternAnalytics)
def get_transaction_patterns_endpoint(
    currency: Optional[str] = Query(default=None, description="Optional ISO currency filter (e.g. INR, USD)"),
    db: Session = Depends(get_db),
):
    """
    Compute pattern intelligence across persisted database records.
    Segments by currency, channel, transaction type, hourly distribution, and top active senders.
    """
    try:
        return compute_transaction_patterns(db=db, currency_filter=currency)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern analytics computation failed: {str(e)}",
        )
