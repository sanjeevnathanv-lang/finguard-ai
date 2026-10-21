from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field
from app.ai.rules import Rule, RuleConclusion

class ConflictRecord(BaseModel):
    conflict_key: str = Field(..., description="The decision/fact key over which rules conflicted")
    competing_rules: List[str] = Field(..., description="Rule IDs that produced competing conclusions")
    competing_values: Dict[str, str] = Field(..., description="Rule ID -> Proposed conclusion value")
    winning_rule_id: str = Field(..., description="Rule ID that won conflict resolution")
    winning_value: str = Field(..., description="Winning conclusion value")
    resolution_strategy: str = Field(..., description="Strategy used: PRIORITY, SPECIFICITY, or DETERMINISTIC_TIEBREAK")
    explanation: str = Field(..., description="Human-readable explanation of how conflict was settled")


class ConflictResolver:
    """Deterministic conflict resolution module for competing rule conclusions."""

    @staticmethod
    def resolve_agenda(rules: List[Rule]) -> List[Rule]:
        """Order activated candidate rules by (priority DESC, specificity DESC, rule_id ASC)."""
        return sorted(
            rules,
            key=lambda r: (r.priority, len(r.conditions), r.rule_id),
            reverse=True,
        )

    @staticmethod
    def resolve_conflicting_conclusions(
        conclusions_by_key: Dict[str, List[Tuple[Rule, RuleConclusion]]]
    ) -> Tuple[Dict[str, Tuple[Rule, RuleConclusion]], List[ConflictRecord]]:
        """
        When multiple rules output different values for the same conclusion key,
        resolve the conflict deterministically using rule priority and specificity.
        """
        resolved: Dict[str, Tuple[Rule, RuleConclusion]] = {}
        conflict_records: List[ConflictRecord] = []

        for key, candidates in conclusions_by_key.items():
            if len(candidates) == 1:
                resolved[key] = candidates[0]
                continue

            # Check if all candidate rules produced the identical value
            unique_values = set(str(c[1].value) for c in candidates)
            if len(unique_values) == 1:
                # Same conclusion produced by multiple rules (consensus)
                # Pick the highest priority rule as the primary source
                best_candidate = max(candidates, key=lambda c: (c[0].priority, len(c[0].conditions)))
                resolved[key] = best_candidate
                continue

            # Genuine conflict: different values proposed for the same key
            competing_values = {rule.rule_id: str(conc.value) for rule, conc in candidates}

            # Sort candidate (Rule, RuleConclusion) by (priority DESC, len(conditions) DESC, rule_id ASC)
            # For rule_id tiebreak, we want ASC alphabetical so reverse sort needs special care
            def sort_key(c: Tuple[Rule, RuleConclusion]):
                rule = c[0]
                # High priority first, high condition count first, lower alphabetical rule_id first
                return (rule.priority, len(rule.conditions), [-ord(ch) for ch in rule.rule_id])

            sorted_candidates = sorted(candidates, key=sort_key, reverse=True)
            winner_rule, winner_conclusion = sorted_candidates[0]
            runner_up_rule, _ = sorted_candidates[1]

            strategy = "PRIORITY"
            if winner_rule.priority == runner_up_rule.priority:
                if len(winner_rule.conditions) > len(runner_up_rule.conditions):
                    strategy = "SPECIFICITY"
                else:
                    strategy = "DETERMINISTIC_TIEBREAK"

            explanation = (
                f"Conflict on '{key}': Rule '{winner_rule.rule_id}' (Priority {winner_rule.priority}, "
                f"{len(winner_rule.conditions)} conditions) superseded '{runner_up_rule.rule_id}' "
                f"(Priority {runner_up_rule.priority}, {len(runner_up_rule.conditions)} conditions) "
                f"via {strategy} strategy. Adopted recommendation: '{winner_conclusion.value}'."
            )

            record = ConflictRecord(
                conflict_key=key,
                competing_rules=[rule.rule_id for rule, _ in candidates],
                competing_values=competing_values,
                winning_rule_id=winner_rule.rule_id,
                winning_value=str(winner_conclusion.value),
                resolution_strategy=strategy,
                explanation=explanation,
            )
            conflict_records.append(record)
            resolved[key] = (winner_rule, winner_conclusion)

        return resolved, conflict_records
