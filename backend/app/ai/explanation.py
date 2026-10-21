from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.ai.conflict_resolution import ConflictRecord

class RuleActivationRecord(BaseModel):
    rule_id: str
    rule_name: str
    cycle: int
    priority: int
    category: str
    conditions_evaluated: List[str]
    derived_facts: Dict[str, Any] = Field(default_factory=dict)
    conclusions: List[Dict[str, Any]] = Field(default_factory=list)
    rationale: str


class InferenceTrace(BaseModel):
    engine_version: str = "1.0.0"
    knowledge_base_version: str = "1.0.0"
    evaluation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_cycles: int = 0
    initial_facts: Dict[str, Any] = Field(default_factory=dict)
    derived_facts: Dict[str, Any] = Field(default_factory=dict)
    activated_rules: List[RuleActivationRecord] = Field(default_factory=list)
    untriggered_rule_ids: List[str] = Field(default_factory=list)
    conflicts_detected: List[ConflictRecord] = Field(default_factory=list)
    final_recommendation: str = "STANDARD_PROCESSING"
    final_conclusions: Dict[str, Any] = Field(default_factory=dict)
    overall_severity: str = "INFORMATIONAL"
    risk_score: float = 0.0  # Heuristic evidence weight aggregation
    human_readable_summary: str = ""

    def generate_summary(self) -> str:
        """Construct an academic, transparent audit explanation of the deduction steps."""
        lines = []
        lines.append(f"Inference complete in {self.total_cycles} cycle(s). {len(self.activated_rules)} rule(s) activated.")

        if self.activated_rules:
            lines.append("Reasoning chain:")
            for act in self.activated_rules:
                lines.append(f"  • [Cycle {act.cycle}] {act.rule_name} ({act.rule_id}, Priority {act.priority}): {act.rationale}")
        else:
            lines.append("  • Baseline parameters verified; no specialized risk rules activated.")

        if self.conflicts_detected:
            lines.append("Conflict resolutions:")
            for conf in self.conflicts_detected:
                lines.append(f"  • {conf.explanation}")

        lines.append(f"Final Decision: {self.final_recommendation} (Severity: {self.overall_severity}).")
        return "\n".join(lines)
