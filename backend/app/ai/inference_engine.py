from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any
from app.ai.facts import FactSet, Fact, FactSource
from app.ai.rules import Rule, RuleConclusion, ConclusionType, Severity
from app.ai.knowledge_base import KnowledgeBase
from app.ai.conflict_resolution import ConflictResolver
from app.ai.explanation import InferenceTrace, RuleActivationRecord

ENGINE_VERSION = "1.0.0"
MAX_INFERENCE_CYCLES = 10

SEVERITY_ORDER = {
    Severity.INFORMATIONAL: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

class ForwardChainingEngine:
    """
    Data-driven forward-chaining expert system inference engine.
    Executes iterative pattern matching, multi-step fact derivation,
    cycle and loop protection, and deterministic conflict resolution.
    """

    def __init__(self, knowledge_base: KnowledgeBase, max_cycles: int = MAX_INFERENCE_CYCLES):
        self.kb = knowledge_base
        self.max_cycles = max_cycles

    def run_inference(self, initial_facts: FactSet) -> InferenceTrace:
        """
        Execute forward-chaining deduction over the working memory.
        Returns a complete, explainable audit trace.
        """
        trace = InferenceTrace(
            engine_version=ENGINE_VERSION,
            knowledge_base_version=self.kb.version,
            initial_facts=initial_facts.to_dict(),
        )

        fired_rules: Set[str] = set()
        conclusions_pool: Dict[str, List[Tuple[Rule, RuleConclusion]]] = defaultdict(list)
        all_candidate_rules = self.kb.active_rules()

        cycle = 0

        while cycle < self.max_cycles:
            cycle += 1
            new_facts_count = 0
            eligible_rules: List[Rule] = []
            evaluation_notes: Dict[str, List[str]] = {}

            # 1. Pattern Matching (Match Phase)
            for rule in all_candidate_rules:
                if rule.rule_id in fired_rules:
                    continue

                is_matched, condition_traces = rule.evaluate(initial_facts)
                evaluation_notes[rule.rule_id] = condition_traces

                if is_matched:
                    eligible_rules.append(rule)

            # Check for quiescence (no more rules match)
            if not eligible_rules:
                break

            # 2. Conflict Resolution on Rule Agenda (Select Phase)
            # Order rules by priority DESC, specificity DESC, rule_id ASC
            ordered_agenda = ConflictResolver.resolve_agenda(eligible_rules)

            # 3. Action Phase (Fire Phase)
            for rule in ordered_agenda:
                fired_rules.add(rule.rule_id)
                rule_derived_facts: Dict[str, Any] = {}
                rule_conclusions_list: List[Dict[str, Any]] = []

                for conclusion in rule.conclusions:
                    # Accumulate for post-inference conflict resolution
                    conclusions_pool[conclusion.key].append((rule, conclusion))
                    rule_conclusions_list.append(conclusion.model_dump())

                    # If conclusion derives a new fact, assert it into working memory
                    if conclusion.conclusion_type == ConclusionType.DERIVED_FACT:
                        # Only assert if not already set to this value to maintain monotonicity
                        current_val = initial_facts.get_value(conclusion.key)
                        if current_val != conclusion.value:
                            new_fact = Fact(
                                name=conclusion.key,
                                value=conclusion.value,
                                data_type="BOOLEAN" if isinstance(conclusion.value, bool) else "STRING",
                                source=FactSource.DERIVED_INFERENCE,
                                confidence=1.0,
                                description=conclusion.message,
                                derived_by_rule_id=rule.rule_id,
                            )
                            initial_facts.add_fact(new_fact)
                            trace.derived_facts[conclusion.key] = conclusion.value
                            rule_derived_facts[conclusion.key] = conclusion.value
                            new_facts_count += 1

                # Record rule activation in audit trace
                activation_record = RuleActivationRecord(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    cycle=cycle,
                    priority=rule.priority,
                    category=rule.category,
                    conditions_evaluated=evaluation_notes.get(rule.rule_id, []),
                    derived_facts=rule_derived_facts,
                    conclusions=rule_conclusions_list,
                    rationale=rule.rationale,
                )
                trace.activated_rules.append(activation_record)

            # If no new facts were derived in this cycle, forward chaining has reached a fixpoint
            if new_facts_count == 0:
                break

        trace.total_cycles = cycle

        # 4. Resolve Conflicting Conclusions
        resolved_conclusions, conflict_records = ConflictResolver.resolve_conflicting_conclusions(conclusions_pool)
        trace.conflicts_detected = conflict_records

        # 5. Compile Final Conclusions & Recommendation
        final_conclusions_dict: Dict[str, Any] = {}
        highest_severity = Severity.INFORMATIONAL
        total_risk_weight = 0.0

        for key, (rule, conclusion) in resolved_conclusions.items():
            final_conclusions_dict[key] = {
                "value": conclusion.value,
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "severity": conclusion.severity.value,
                "weight": conclusion.weight,
                "message": conclusion.message,
            }
            if SEVERITY_ORDER[conclusion.severity] > SEVERITY_ORDER[highest_severity]:
                highest_severity = conclusion.severity
            total_risk_weight += conclusion.weight

        trace.final_conclusions = final_conclusions_dict
        trace.overall_severity = highest_severity.value
        trace.risk_score = round(min(10.0, total_risk_weight), 2)

        # Primary operational recommendation
        if "REVIEW_DECISION" in resolved_conclusions:
            trace.final_recommendation = str(resolved_conclusions["REVIEW_DECISION"][1].value)
        elif trace.activated_rules:
            trace.final_recommendation = "CONTEXTUAL_ANOMALY_REVIEW"
        else:
            trace.final_recommendation = "STANDARD_PROCESSING"

        # Record untriggered rules
        all_rule_ids = {r.rule_id for r in all_candidate_rules}
        trace.untriggered_rule_ids = sorted(list(all_rule_ids - fired_rules))
        trace.human_readable_summary = trace.generate_summary()

        return trace
