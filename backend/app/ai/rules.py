from enum import Enum
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Dict
from pydantic import BaseModel, Field
from app.ai.facts import FactSet, Fact, FactSource

class ConditionOperator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    IN = "IN"
    NOT_IN = "NOT_IN"
    EXISTS = "EXISTS"
    DOES_NOT_EXIST = "DOES_NOT_EXIST"
    IS_EMPTY = "IS_EMPTY"
    CONTAINS = "CONTAINS"


class LogicalOperator(str, Enum):
    ALL = "ALL"  # Logical AND
    ANY = "ANY"  # Logical OR


class ConclusionType(str, Enum):
    DERIVED_FACT = "DERIVED_FACT"
    RECOMMENDATION = "RECOMMENDATION"
    DATA_QUALITY_ALERT = "DATA_QUALITY_ALERT"
    RISK_SIGNAL = "RISK_SIGNAL"


class Severity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleCondition(BaseModel):
    fact_name: str = Field(..., description="Name of the fact to evaluate")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Any = Field(default=None, description="Expected comparison value")

    def evaluate(self, fact_set: FactSet) -> Tuple[bool, str]:
        """Safely evaluate this condition against the working memory."""
        fact = fact_set.get_fact(self.fact_name)
        actual = fact.value if fact is not None else None

        # Existence checks
        if self.operator == ConditionOperator.EXISTS:
            matched = actual is not None and actual != ""
            reason = f"Fact '{self.fact_name}' {'exists' if matched else 'is missing/null'}"
            return matched, reason

        if self.operator == ConditionOperator.DOES_NOT_EXIST or self.operator == ConditionOperator.IS_EMPTY:
            matched = actual is None or actual == "" or (isinstance(actual, (list, dict)) and len(actual) == 0)
            reason = f"Fact '{self.fact_name}' {'is empty/missing' if matched else f'has value: {actual}'}"
            return matched, reason

        # If fact is missing, condition cannot be satisfied
        if actual is None:
            return False, f"Fact '{self.fact_name}' is missing (UNKNOWN)"

        try:
            # Numeric comparisons (handle Decimal/int/float cleanly)
            if self.operator in (
                ConditionOperator.GREATER_THAN,
                ConditionOperator.LESS_THAN,
                ConditionOperator.GREATER_EQUAL,
                ConditionOperator.LESS_EQUAL,
            ):
                num_actual = Decimal(str(actual))
                num_target = Decimal(str(self.value))

                if self.operator == ConditionOperator.GREATER_THAN:
                    matched = num_actual > num_target
                    op_str = ">"
                elif self.operator == ConditionOperator.LESS_THAN:
                    matched = num_actual < num_target
                    op_str = "<"
                elif self.operator == ConditionOperator.GREATER_EQUAL:
                    matched = num_actual >= num_target
                    op_str = ">="
                else:
                    matched = num_actual <= num_target
                    op_str = "<="

                reason = f"Fact '{self.fact_name}' ({actual}) {op_str} target ({self.value}) -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

            # Equality & Membership
            if self.operator == ConditionOperator.EQUALS:
                matched = str(actual).strip().upper() == str(self.value).strip().upper()
                reason = f"Fact '{self.fact_name}' ({actual}) == ({self.value}) -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

            if self.operator == ConditionOperator.NOT_EQUALS:
                matched = str(actual).strip().upper() != str(self.value).strip().upper()
                reason = f"Fact '{self.fact_name}' ({actual}) != ({self.value}) -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

            if self.operator == ConditionOperator.IN:
                target_list = [str(x).strip().upper() for x in (self.value if isinstance(self.value, list) else [self.value])]
                matched = str(actual).strip().upper() in target_list
                reason = f"Fact '{self.fact_name}' ({actual}) in {target_list} -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

            if self.operator == ConditionOperator.NOT_IN:
                target_list = [str(x).strip().upper() for x in (self.value if isinstance(self.value, list) else [self.value])]
                matched = str(actual).strip().upper() not in target_list
                reason = f"Fact '{self.fact_name}' ({actual}) not in {target_list} -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

            if self.operator == ConditionOperator.CONTAINS:
                matched = str(self.value).lower() in str(actual).lower()
                reason = f"Fact '{self.fact_name}' contains '{self.value}' -> {'Matched' if matched else 'Unmatched'}"
                return matched, reason

        except Exception as e:
            return False, f"Evaluation error on fact '{self.fact_name}': {str(e)}"

        return False, f"Unsupported operator '{self.operator}'"


class RuleConclusion(BaseModel):
    conclusion_type: ConclusionType = Field(..., description="Type of conclusion")
    key: str = Field(..., description="Fact key to derive or recommendation code")
    value: Any = Field(..., description="Value to derive or recommendation payload")
    severity: Severity = Field(default=Severity.MEDIUM)
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Relative evidentiary weight")
    message: str = Field(..., description="Human-readable rationale for conclusion")


class Rule(BaseModel):
    rule_id: str = Field(..., description="Unique stable rule identifier")
    version: str = Field(default="1.0.0", description="Semantic rule version")
    name: str = Field(..., description="Readable rule title")
    description: str = Field(..., description="Detailed description of rule domain logic")
    category: str = Field(default="GENERAL", description="Rule category/domain grouping")
    conditions: List[RuleCondition] = Field(..., min_length=1)
    logical_operator: LogicalOperator = Field(default=LogicalOperator.ALL)
    conclusions: List[RuleConclusion] = Field(..., min_length=1)
    priority: int = Field(default=50, ge=1, le=100, description="Priority for conflict resolution (higher = more specific)")
    rationale: str = Field(default="", description="Domain reason and regulatory context")
    is_active: bool = Field(default=True)

    def evaluate(self, fact_set: FactSet) -> Tuple[bool, List[str]]:
        """Evaluate rule conditions against working memory."""
        if not self.is_active:
            return False, [f"Rule '{self.rule_id}' is inactive"]

        condition_results = [cond.evaluate(fact_set) for cond in self.conditions]
        matches = [m for m, _ in condition_results]
        explanations = [exp for _, exp in condition_results]

        if self.logical_operator == LogicalOperator.ALL:
            fired = all(matches)
        else:
            fired = any(matches)

        return fired, explanations
