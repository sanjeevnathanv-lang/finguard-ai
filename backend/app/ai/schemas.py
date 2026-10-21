from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.ai.rules import ConditionOperator, LogicalOperator, ConclusionType, Severity

class ConditionSchema(BaseModel):
    fact_name: str
    operator: ConditionOperator
    value: Any = None


class ConclusionSchema(BaseModel):
    conclusion_type: ConclusionType
    key: str
    value: Any
    severity: Severity
    weight: float
    message: str


class RuleSchema(BaseModel):
    rule_id: str
    version: str
    name: str
    description: str
    category: str
    priority: int
    logical_operator: LogicalOperator
    conditions: List[ConditionSchema]
    conclusions: List[ConclusionSchema]
    rationale: str
    is_active: bool


class FactInputSchema(BaseModel):
    name: str
    value: Any
    description: Optional[str] = ""


class FactEvaluationRequest(BaseModel):
    facts: List[FactInputSchema] = Field(..., min_length=1)


class RuleActivationDTO(BaseModel):
    rule_id: str
    rule_name: str
    cycle: int
    priority: int
    category: str
    conditions_evaluated: List[str]
    derived_facts: Dict[str, Any]
    conclusions: List[Dict[str, Any]]
    rationale: str


class ConflictRecordDTO(BaseModel):
    conflict_key: str
    competing_rules: List[str]
    competing_values: Dict[str, str]
    winning_rule_id: str
    winning_value: str
    resolution_strategy: str
    explanation: str


class InferenceTraceDTO(BaseModel):
    engine_version: str
    knowledge_base_version: str
    evaluation_timestamp: datetime
    total_cycles: int
    initial_facts: Dict[str, Any]
    derived_facts: Dict[str, Any]
    activated_rules: List[RuleActivationDTO]
    untriggered_rule_ids: List[str]
    conflicts_detected: List[ConflictRecordDTO]
    final_recommendation: str
    final_conclusions: Dict[str, Any]
    overall_severity: str
    risk_score: float
    human_readable_summary: str


class AssessmentResponse(BaseModel):
    assessment_id: int
    transaction_id: Optional[int]
    transaction_reference: Optional[str]
    final_recommendation: str
    overall_severity: str
    risk_score: float
    rules_triggered_count: int
    created_at: datetime
    trace: InferenceTraceDTO
    hybrid_report: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
