from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

VALID_CASE_STATUSES = {"OPEN", "IN_REVIEW", "WAITING_FOR_INFORMATION", "CLOSED"}
VALID_CASE_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_DISPOSITIONS = {
    "UNVERIFIED_SUSPICION",
    "CONFIRMED_LEGITIMATE",
    "CONFIRMED_FRAUD",
    "INCONCLUSIVE",
}

VALID_STATUS_TRANSITIONS: Dict[str, set] = {
    "OPEN": {"IN_REVIEW", "WAITING_FOR_INFORMATION", "CLOSED"},
    "IN_REVIEW": {"OPEN", "WAITING_FOR_INFORMATION", "CLOSED"},
    "WAITING_FOR_INFORMATION": {"OPEN", "IN_REVIEW", "CLOSED"},
    "CLOSED": {"OPEN", "IN_REVIEW"},  # Reopening
}


class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Factual, concise case title")
    summary: Optional[str] = Field(default=None, description="Factual context or background summary of the investigation")
    priority: str = Field(
        default="MEDIUM",
        description="Review triage priority (LOW, MEDIUM, HIGH, CRITICAL). Not a confirmed fraud label."
    )
    assigned_reviewer: Optional[str] = Field(default=None, max_length=128, description="Name or identifier of assigned risk investigator")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        upper = v.upper()
        if upper not in VALID_CASE_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(VALID_CASE_PRIORITIES)}")
        return upper


class CaseCreate(CaseBase):
    initial_transaction_ids: Optional[List[int]] = Field(
        default_factory=list,
        description="Optional list of transaction database IDs to associate immediately"
    )
    linking_reason: Optional[str] = Field(
        default="Initial transaction flagged for review during case creation",
        max_length=255
    )
    initial_note: Optional[str] = Field(
        default=None,
        description="Optional opening investigator note"
    )


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    summary: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_reviewer: Optional[str] = Field(default=None, max_length=128)
    reviewer_notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        upper = v.upper()
        if upper not in VALID_CASE_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_CASE_STATUSES)}")
        return upper

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        upper = v.upper()
        if upper not in VALID_CASE_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(VALID_CASE_PRIORITIES)}")
        return upper


class CaseCloseRequest(BaseModel):
    final_disposition: str = Field(
        ...,
        description="Final reviewer disposition: UNVERIFIED_SUSPICION, CONFIRMED_LEGITIMATE, CONFIRMED_FRAUD, INCONCLUSIVE"
    )
    disposition_notes: str = Field(
        ...,
        min_length=5,
        description="Mandatory reviewer explanation justifying the final disposition"
    )
    reviewer_name: Optional[str] = Field(default=None, max_length=128)

    @field_validator("final_disposition")
    @classmethod
    def validate_disposition(cls, v: str) -> str:
        upper = v.upper()
        if upper not in VALID_DISPOSITIONS:
            raise ValueError(f"final_disposition must be one of {sorted(VALID_DISPOSITIONS)}")
        return upper


class CaseNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, description="Investigator note or comment text")
    author: Optional[str] = Field(default="Reviewer", max_length=128)


class CaseTransactionLinkRequest(BaseModel):
    transaction_id: int = Field(..., gt=0, description="Database ID of the transaction to link")
    linking_reason: Optional[str] = Field(
        default="Manually linked by investigator during case examination",
        max_length=255
    )


class TimelineEventRead(BaseModel):
    id: int
    case_id: int
    event_type: str
    title: str
    description: Optional[str] = None
    source: str
    actor: Optional[str] = None
    event_timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseTransactionRead(BaseModel):
    id: int
    transaction_id: int
    transaction_reference: str
    timestamp: datetime
    amount: Decimal
    currency: str
    transaction_type: str
    channel: str
    status: str
    sender_reference: Optional[str] = None
    receiver_reference: Optional[str] = None
    linking_reason: Optional[str] = None
    linked_at: datetime
    latest_assessment: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseRead(BaseModel):
    id: int
    case_reference: str
    title: str
    summary: Optional[str] = None
    status: str
    priority: str
    assigned_reviewer: Optional[str] = None
    reviewer_notes: Optional[str] = None
    final_disposition: Optional[str] = None
    disposition_notes: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    linked_transactions_count: int = 0
    events_count: int = 0
    transactions: Optional[List[CaseTransactionRead]] = None
    events: Optional[List[TimelineEventRead]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    items: List[CaseRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class RelatedTransactionRead(BaseModel):
    transaction_id: int
    transaction_reference: str
    timestamp: datetime
    amount: Decimal
    currency: str
    transaction_type: str
    channel: str
    status: str
    sender_reference: Optional[str] = None
    receiver_reference: Optional[str] = None
    relationship_reasons: List[str]
    match_strength: str  # "HIGH", "MEDIUM", "INFORMATIONAL"
    is_already_linked: bool


class CaseExportResponse(BaseModel):
    case_reference: str
    title: str
    status: str
    priority: str
    assigned_reviewer: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None
    final_disposition: Optional[str] = None
    disposition_notes: Optional[str] = None
    total_linked_transactions: int
    total_timeline_events: int
    executive_summary: str
    report_markdown: str
    report_json: Dict[str, Any]
