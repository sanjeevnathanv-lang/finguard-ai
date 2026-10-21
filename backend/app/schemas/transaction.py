import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

VALID_TRANSACTION_TYPES = {"PAYMENT", "TRANSFER", "WITHDRAWAL", "DEPOSIT", "PURCHASE", "REFUND"}
VALID_CHANNELS = {"ONLINE", "MOBILE_APP", "ATM", "POS", "BRANCH", "API"}
VALID_STATUSES = {"COMPLETED", "PENDING", "FLAGGED", "FAILED", "CANCELLED"}
VALID_CURRENCIES = {"INR", "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "SGD", "AED", "CHF"}

def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has timezone UTC or convert naive datetime to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TransactionBase(BaseModel):
    reference: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=64,
        description="Unique transaction reference code",
        examples=["TXN-2026-0001"]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Transaction timestamp in UTC"
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Monetary transaction amount (> 0)",
        examples=[1450.50]
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="3-letter ISO 4217 currency code",
        examples=["INR"]
    )
    sender_reference: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Sender token or reference (masked/pseudonymized)",
        examples=["SND-8821"]
    )
    receiver_reference: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Receiver token or merchant reference",
        examples=["RCV-4091"]
    )
    transaction_type: str = Field(
        ...,
        description="Type of transaction",
        examples=["PAYMENT"]
    )
    channel: str = Field(
        ...,
        description="Delivery channel",
        examples=["MOBILE_APP"]
    )
    status: str = Field(
        default="COMPLETED",
        description="Current transaction lifecycle status",
        examples=["COMPLETED"]
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional operational or context notes"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Amount must be a finite numerical value.")
        if v <= 0:
            raise ValueError("Amount must be strictly greater than 0.")
        # Round to 4 decimal places for currency compatibility
        return round(v, 4)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("Currency must be a valid 3-letter alphabetic code.")
        if code not in VALID_CURRENCIES:
            raise ValueError(f"Currency '{code}' is not in configured currencies: {sorted(list(VALID_CURRENCIES))}")
        return code

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        tt = v.strip().upper()
        if tt not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type '{v}'. Allowed: {sorted(list(VALID_TRANSACTION_TYPES))}")
        return tt

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        ch = v.strip().upper()
        if ch not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel '{v}'. Allowed: {sorted(list(VALID_CHANNELS))}")
        return ch

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        st = v.strip().upper()
        if st not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed: {sorted(list(VALID_STATUSES))}")
        return st


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    reference: str
    dataset_provenance: str
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionPaginatedResponse(BaseModel):
    items: List[TransactionRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class CSVRowError(BaseModel):
    row_number: int
    field: Optional[str] = None
    error_message: str


class CSVUploadResponse(BaseModel):
    import_reference: str
    filename: str
    total_rows: int
    imported_rows: int
    skipped_rows: int
    rejected_rows: int
    errors: List[CSVRowError]
    duration_ms: float
    message: str


class DashboardMetricsResponse(BaseModel):
    total_transactions: int
    flagged_transactions: int = 0
    status_distribution: Dict[str, int]
    volume_by_currency: Dict[str, float]
    recent_transactions_count: int
    latest_transaction_timestamp: Optional[datetime]
    dataset_summary: Dict[str, int]
    system_health: str
