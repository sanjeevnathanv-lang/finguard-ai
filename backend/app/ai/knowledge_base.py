from typing import Dict, List, Optional
from app.ai.rules import (
    Rule,
    RuleCondition,
    ConditionOperator,
    RuleConclusion,
    ConclusionType,
    Severity,
    LogicalOperator,
)

KNOWLEDGE_BASE_VERSION = "1.0.0"

# Real-time transaction surveillance threshold constants
HIGH_AMOUNT_THRESHOLDS = {
    "INR": 200000.0,  # 2 Lakhs INR
    "USD": 2500.0,
    "EUR": 2500.0,
    "GBP": 2000.0,
}

EXPERT_RULES: List[Rule] = [
    # Rule 1: Data Integrity / Missing Information Review
    Rule(
        rule_id="RULE_DATA_DEFICIENCY",
        version="1.0.0",
        name="Missing Counterparty Reference",
        description="Identifies transactions lacking an identifiable sender or receiver reference.",
        category="DATA_INTEGRITY",
        priority=30,
        logical_operator=LogicalOperator.ANY,
        conditions=[
            RuleCondition(fact_name="sender_reference", operator=ConditionOperator.DOES_NOT_EXIST),
            RuleCondition(fact_name="receiver_reference", operator=ConditionOperator.DOES_NOT_EXIST),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="has_data_deficiency",
                value=True,
                severity=Severity.MEDIUM,
                weight=1.5,
                message="Transaction lacks full counterparty provenance details.",
            ),
            RuleConclusion(
                conclusion_type=ConclusionType.DATA_QUALITY_ALERT,
                key="INCOMPLETE_METADATA",
                value="MANUAL_METADATA_REVIEW",
                severity=Severity.LOW,
                weight=1.0,
                message="Flagged for counterparty verification due to missing reference tokens.",
            ),
        ],
        rationale="Anti-Money Laundering (AML) travel rules require identifiable counterparty provenance.",
    ),

    # Rule 2: Amount Contextual Anomaly (INR high amount benchmark)
    Rule(
        rule_id="RULE_HIGH_AMOUNT_INR",
        version="1.0.0",
        name="Elevated Amount Benchmark (INR)",
        description="Flags Indian Rupee transactions exceeding 200,000 INR for contextual review.",
        category="AMOUNT_ANOMALY",
        priority=40,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="currency", operator=ConditionOperator.EQUALS, value="INR"),
            RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_EQUAL, value=HIGH_AMOUNT_THRESHOLDS["INR"]),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="is_high_value_transaction",
                value=True,
                severity=Severity.MEDIUM,
                weight=2.0,
                message="Transaction monetary value exceeds standard individual transaction threshold (INR 200,000).",
            ),
            RuleConclusion(
                conclusion_type=ConclusionType.RISK_SIGNAL,
                key="HIGH_VALUE_THRESHOLD",
                value="ELEVATED_AMOUNT",
                severity=Severity.MEDIUM,
                weight=2.0,
                message="High monetary transaction volume warrants source-of-funds verification.",
            ),
        ],
        rationale="AML and financial surveillance compliance rule modeling large-value transaction reporting guidelines.",
    ),

    # Rule 3: Amount Contextual Anomaly (Foreign Currencies: USD/EUR/GBP)
    Rule(
        rule_id="RULE_HIGH_AMOUNT_FX",
        version="1.0.0",
        name="Elevated Foreign Currency Transaction",
        description="Flags cross-border or foreign currency transactions exceeding 2,500 units.",
        category="AMOUNT_ANOMALY",
        priority=40,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="currency", operator=ConditionOperator.IN, value=["USD", "EUR", "GBP"]),
            RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_EQUAL, value=2500.0),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="is_high_value_transaction",
                value=True,
                severity=Severity.MEDIUM,
                weight=2.0,
                message="Cross-border or FX transaction exceeds 2,500 unit threshold.",
            ),
            RuleConclusion(
                conclusion_type=ConclusionType.RISK_SIGNAL,
                key="HIGH_VALUE_FX",
                value="ELEVATED_FX_AMOUNT",
                severity=Severity.MEDIUM,
                weight=2.0,
                message="Substantial foreign currency volume flagged for exchange compliance.",
            ),
        ],
        rationale="Foreign exchange reporting guidelines require contextual origin review.",
    ),

    # Rule 4: Multi-Step Derivation: Late Night High Value
    # Satisfied when Rule 2 or 3 has derived `is_high_value_transaction == True` AND the hour is late night
    Rule(
        rule_id="RULE_LATE_NIGHT_HIGH_VALUE",
        version="1.0.0",
        name="Off-Hours High-Value Anomaly",
        description="Multi-step rule: High-value transaction executed during atypical late-night hours (1 AM to 4 AM).",
        category="BEHAVIORAL_PATTERN",
        priority=70,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="is_high_value_transaction", operator=ConditionOperator.EQUALS, value=True),
            RuleCondition(fact_name="hour_of_day", operator=ConditionOperator.IN, value=[1, 2, 3, 4]),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="is_critical_temporal_anomaly",
                value=True,
                severity=Severity.HIGH,
                weight=3.5,
                message="Compound risk: High-value transaction executed during low-activity off-hours window.",
            ),
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="HUMAN_SUPERVISORY_REVIEW",
                severity=Severity.HIGH,
                weight=3.5,
                message="Recommend senior analyst investigation: large funds transfer initiated during anomalous night window.",
            ),
        ],
        rationale="Atypical execution hours combined with peak financial limits represent elevated risk requiring dual authorization.",
    ),

    # Rule 5: Rapid Frequency Burst (Velocity Alert)
    Rule(
        rule_id="RULE_HIGH_VELOCITY_BURST",
        version="1.0.0",
        name="Rapid Account Transaction Velocity",
        description="Detects multiple transactions initiated by the same account within a short 1-hour window.",
        category="VELOCITY_ALERT",
        priority=60,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="sender_txn_count_1h", operator=ConditionOperator.GREATER_EQUAL, value=3),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="rapid_velocity_detected",
                value=True,
                severity=Severity.HIGH,
                weight=3.0,
                message="Account triggered 3 or more operations within 60 minutes.",
            ),
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="VELOCITY_COOLDOWN_VERIFICATION",
                severity=Severity.HIGH,
                weight=3.0,
                message="Account velocity burst detected. Verify customer device telemetry and confirm transaction intent.",
            ),
        ],
        rationale="Rapid transaction bursts often indicate scripted bot attacks or credential stuffing.",
    ),

    # Rule 6: Compound Synthesis: Rapid Velocity + Off-Hours
    Rule(
        rule_id="RULE_COMPOUND_HIGH_RISK_SYNDROME",
        version="1.0.0",
        name="Compound Critical Escalation",
        description="High-priority rule: Combines derived rapid velocity with critical temporal or value anomaly.",
        category="SYNTHESIS",
        priority=90,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="rapid_velocity_detected", operator=ConditionOperator.EQUALS, value=True),
            RuleCondition(fact_name="is_critical_temporal_anomaly", operator=ConditionOperator.EQUALS, value=True),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="EXPEDITED_SECURITY_INTERVENTION",
                severity=Severity.CRITICAL,
                weight=5.0,
                message="Compound signals triggered: Rapid burst velocity coupled with off-hours peak transfer. Recommend customer callback before settlement.",
            ),
        ],
        rationale="Highest confidence composite signature: concurrent velocity and nocturnal high-value transfers.",
    ),

    # Rule 7: Standard Low-Risk Clearance
    Rule(
        rule_id="RULE_STANDARD_CLEARANCE",
        version="1.0.0",
        name="Routine Operational Profile",
        description="Validates transactions adhering to nominal amounts, normal business hours, and zero velocity alerts.",
        category="ROUTINE_PROFILE",
        priority=20,
        logical_operator=LogicalOperator.ALL,
        conditions=[
            RuleCondition(fact_name="amount", operator=ConditionOperator.LESS_EQUAL, value=25000.0),
            RuleCondition(fact_name="hour_of_day", operator=ConditionOperator.IN, value=list(range(6, 23))),
            RuleCondition(fact_name="sender_txn_count_1h", operator=ConditionOperator.LESS_THAN, value=3),
            RuleCondition(fact_name="sender_reference", operator=ConditionOperator.EXISTS),
            RuleCondition(fact_name="receiver_reference", operator=ConditionOperator.EXISTS),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="STANDARD_PROCESSING",
                severity=Severity.INFORMATIONAL,
                weight=1.0,
                message="Nominal parameters confirmed: daylight hours, known counterparty references, and bounded transaction value.",
            ),
        ],
        rationale="Straight-through processing standard for nominal consumer payments.",
    ),
]


class KnowledgeBase:
    """Repository storing domain rules, semantic versions, and validation logic."""

    def __init__(self, rules: Optional[List[Rule]] = None, version: str = KNOWLEDGE_BASE_VERSION):
        self.version = version
        self._rules: Dict[str, Rule] = {}
        for rule in (rules or EXPERT_RULES):
            self.register_rule(rule)

    def register_rule(self, rule: Rule) -> None:
        self.validate_rule(rule)
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def all_rules(self) -> List[Rule]:
        return list(self._rules.values())

    def active_rules(self) -> List[Rule]:
        return [r for r in self._rules.values() if r.is_active]

    @staticmethod
    def validate_rule(rule: Rule) -> None:
        if not rule.rule_id or not rule.rule_id.strip():
            raise ValueError("Rule must have a non-empty rule_id.")
        if not rule.conditions:
            raise ValueError(f"Rule '{rule.rule_id}' must define at least one condition.")
        if not rule.conclusions:
            raise ValueError(f"Rule '{rule.rule_id}' must define at least one conclusion.")
        if rule.priority < 1 or rule.priority > 100:
            raise ValueError(f"Rule '{rule.rule_id}' priority must be between 1 and 100.")
