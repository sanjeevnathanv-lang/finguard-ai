import json
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.ai.knowledge_base import KnowledgeBase
from app.ai.schemas import (
    RuleSchema,
    FactEvaluationRequest,
    InferenceTraceDTO,
)
from app.services.assessment_service import default_knowledge_base, evaluate_custom_facts

router = APIRouter(prefix="/expert-system", tags=["expert-system"])

@router.get("/rules", response_model=List[RuleSchema])
def list_rules():
    """List all registered domain rules in the active knowledge base."""
    return [rule.model_dump() for rule in default_knowledge_base.all_rules()]


@router.get("/rules/{rule_id}", response_model=RuleSchema)
def get_rule(rule_id: str):
    """Retrieve details, conditions, and rationale for a single rule."""
    rule = default_knowledge_base.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found in active knowledge base."
        )
    return rule.model_dump()


@router.post("/evaluate", response_model=InferenceTraceDTO)
def evaluate_facts(payload: FactEvaluationRequest):
    """
    Directly evaluate an input fact set against the forward-chaining inference engine.
    Safe, deterministic execution without executing arbitrary code.
    """
    try:
        facts_data = [fact.model_dump() for fact in payload.facts]
        trace = evaluate_custom_facts(facts_data)
        return trace.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inference evaluation failed: {str(e)}"
        )
