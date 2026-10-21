import pytest
from decimal import Decimal
from app.ai.facts import Fact, FactSet, FactSource
from app.ai.rules import (
    Rule,
    RuleCondition,
    RuleConclusion,
    ConditionOperator,
    LogicalOperator,
    ConclusionType,
    Severity,
)
from app.ai.knowledge_base import KnowledgeBase
from app.ai.conflict_resolution import ConflictResolver
from app.ai.inference_engine import ForwardChainingEngine

def test_condition_operators_evaluation():
    """Verify all condition comparison operators with numeric, string, and set types."""
    facts = FactSet([
        Fact(name="amount", value=1500.0),
        Fact(name="status", value="COMPLETED"),
        Fact(name="currency", value="INR"),
        Fact(name="tags", value=["VIP", "DOMESTIC"]),
        Fact(name="empty_field", value=None),
    ])

    # EQUALS
    c_eq = RuleCondition(fact_name="status", operator=ConditionOperator.EQUALS, value="COMPLETED")
    assert c_eq.evaluate(facts)[0] is True

    # NOT_EQUALS
    c_neq = RuleCondition(fact_name="status", operator=ConditionOperator.NOT_EQUALS, value="FAILED")
    assert c_neq.evaluate(facts)[0] is True

    # GREATER_THAN / LESS_THAN
    c_gt = RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_THAN, value=1000)
    assert c_gt.evaluate(facts)[0] is True
    c_lt = RuleCondition(fact_name="amount", operator=ConditionOperator.LESS_THAN, value=2000)
    assert c_lt.evaluate(facts)[0] is True

    # GREATER_EQUAL / LESS_EQUAL
    c_ge = RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_EQUAL, value=1500)
    assert c_ge.evaluate(facts)[0] is True
    c_le = RuleCondition(fact_name="amount", operator=ConditionOperator.LESS_EQUAL, value=1500)
    assert c_le.evaluate(facts)[0] is True

    # IN / NOT_IN
    c_in = RuleCondition(fact_name="currency", operator=ConditionOperator.IN, value=["INR", "USD"])
    assert c_in.evaluate(facts)[0] is True
    c_nin = RuleCondition(fact_name="currency", operator=ConditionOperator.NOT_IN, value=["EUR", "GBP"])
    assert c_nin.evaluate(facts)[0] is True

    # EXISTS / DOES_NOT_EXIST
    c_ex = RuleCondition(fact_name="currency", operator=ConditionOperator.EXISTS)
    assert c_ex.evaluate(facts)[0] is True
    c_nex = RuleCondition(fact_name="empty_field", operator=ConditionOperator.DOES_NOT_EXIST)
    assert c_nex.evaluate(facts)[0] is True
    c_missing = RuleCondition(fact_name="nonexistent_key", operator=ConditionOperator.DOES_NOT_EXIST)
    assert c_missing.evaluate(facts)[0] is True

def test_logical_operators_all_and_any():
    """Verify ALL (AND) vs ANY (OR) logical combination semantics."""
    facts = FactSet([
        Fact(name="currency", value="INR"),
        Fact(name="amount", value=500),
    ])

    # Rule with ALL (both must match: amount > 1000 is False, so overall is False)
    rule_all = Rule(
        rule_id="RULE_TEST_ALL",
        name="Test ALL",
        description="",
        conditions=[
            RuleCondition(fact_name="currency", operator=ConditionOperator.EQUALS, value="INR"),
            RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_THAN, value=1000),
        ],
        logical_operator=LogicalOperator.ALL,
        conclusions=[RuleConclusion(conclusion_type=ConclusionType.RECOMMENDATION, key="DECISION", value="FAIL", message="")],
    )
    assert rule_all.evaluate(facts)[0] is False

    # Rule with ANY (currency == INR matches, so overall is True)
    rule_any = Rule(
        rule_id="RULE_TEST_ANY",
        name="Test ANY",
        description="",
        conditions=[
            RuleCondition(fact_name="currency", operator=ConditionOperator.EQUALS, value="INR"),
            RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_THAN, value=1000),
        ],
        logical_operator=LogicalOperator.ANY,
        conclusions=[RuleConclusion(conclusion_type=ConclusionType.RECOMMENDATION, key="DECISION", value="PASS", message="")],
    )
    assert rule_any.evaluate(facts)[0] is True

def test_missing_facts_do_not_falsely_match():
    """Ensure missing facts are treated as UNKNOWN and never evaluate as true."""
    facts = FactSet([Fact(name="amount", value=500)])

    cond = RuleCondition(fact_name="sender_account_age_days", operator=ConditionOperator.GREATER_THAN, value=30)
    matched, reason = cond.evaluate(facts)
    assert matched is False
    assert "missing" in reason.lower()

def test_multi_step_inference_chain():
    """
    Test genuine forward-chaining deduction across multiple cycles:
    Cycle 1: Rule 1 fires based on initial facts, derives Fact 'risk_level_elevated'
    Cycle 2: Rule 2 matches on 'risk_level_elevated' and derives final Recommendation
    """
    rule1 = Rule(
        rule_id="RULE_STEP_1",
        name="Derive High Risk",
        description="",
        priority=50,
        conditions=[
            RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_THAN, value=100000),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="is_high_risk_amount",
                value=True,
                severity=Severity.HIGH,
                message="Amount exceeds threshold",
            )
        ],
    )

    rule2 = Rule(
        rule_id="RULE_STEP_2",
        name="Escalate On Derived Risk",
        description="",
        priority=80,
        conditions=[
            RuleCondition(fact_name="is_high_risk_amount", operator=ConditionOperator.EQUALS, value=True),
            RuleCondition(fact_name="channel", operator=ConditionOperator.EQUALS, value="ONLINE"),
        ],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="MANUAL_SUPERVISOR_INTERVENTION",
                severity=Severity.HIGH,
                message="Escalate compound risk",
            )
        ],
    )

    kb = KnowledgeBase(rules=[rule1, rule2])
    engine = ForwardChainingEngine(kb)

    working_memory = FactSet([
        Fact(name="amount", value=250000),
        Fact(name="channel", value="ONLINE"),
    ])

    trace = engine.run_inference(working_memory)

    # Must take 2 cycles of deduction
    assert trace.total_cycles >= 2
    assert len(trace.activated_rules) == 2
    assert trace.activated_rules[0].rule_id == "RULE_STEP_1"
    assert trace.activated_rules[1].rule_id == "RULE_STEP_2"
    assert trace.derived_facts.get("is_high_risk_amount") is True
    assert trace.final_recommendation == "MANUAL_SUPERVISOR_INTERVENTION"

def test_deterministic_conflict_resolution():
    """
    When competing rules produce differing conclusions for REVIEW_DECISION:
    Rule A (priority 30): STANDARD_PROCESSING
    Rule B (priority 75): SENIOR_INVESTIGATOR_REVIEW
    Rule B must win deterministically, and the conflict must be recorded.
    """
    rule_a = Rule(
        rule_id="RULE_LOW_PRIO",
        name="Low Priority Rule",
        description="",
        priority=30,
        conditions=[RuleCondition(fact_name="currency", operator=ConditionOperator.EQUALS, value="INR")],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="STANDARD_PROCESSING",
                severity=Severity.INFORMATIONAL,
                message="Standard routine flow",
            )
        ],
    )

    rule_b = Rule(
        rule_id="RULE_HIGH_PRIO",
        name="High Priority Anomaly",
        description="",
        priority=75,
        conditions=[RuleCondition(fact_name="amount", operator=ConditionOperator.GREATER_THAN, value=50000)],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.RECOMMENDATION,
                key="REVIEW_DECISION",
                value="SENIOR_INVESTIGATOR_REVIEW",
                severity=Severity.HIGH,
                message="Elevated risk anomaly",
            )
        ],
    )

    kb = KnowledgeBase(rules=[rule_a, rule_b])
    engine = ForwardChainingEngine(kb)

    facts = FactSet([
        Fact(name="currency", value="INR"),
        Fact(name="amount", value=99000),
    ])

    trace = engine.run_inference(facts)

    # Higher priority rule wins the decision
    assert trace.final_recommendation == "SENIOR_INVESTIGATOR_REVIEW"
    # Conflict is explicitly documented
    assert len(trace.conflicts_detected) == 1
    conflict = trace.conflicts_detected[0]
    assert conflict.conflict_key == "REVIEW_DECISION"
    assert conflict.winning_rule_id == "RULE_HIGH_PRIO"
    assert "superseded" in conflict.explanation.lower()

def test_repeated_firing_and_cycle_limit_protection():
    """Ensure engine cannot loop infinitely if a rule derives existing facts."""
    loop_rule = Rule(
        rule_id="RULE_POTENTIAL_LOOP",
        name="Loop Candidate",
        description="",
        priority=50,
        conditions=[RuleCondition(fact_name="counter", operator=ConditionOperator.GREATER_THAN, value=0)],
        conclusions=[
            RuleConclusion(
                conclusion_type=ConclusionType.DERIVED_FACT,
                key="counter",
                value=1,
                message="Re-assert same value",
            )
        ],
    )

    kb = KnowledgeBase(rules=[loop_rule])
    engine = ForwardChainingEngine(kb, max_cycles=5)
    facts = FactSet([Fact(name="counter", value=1)])

    trace = engine.run_inference(facts)
    # The rule fires once, sets counter=1 (no change), and inference halts cleanly
    assert len(trace.activated_rules) == 1
    assert trace.total_cycles <= 2

def test_api_list_and_get_rules(client):
    """Test /api/expert-system/rules endpoints."""
    res = client.get("/api/expert-system/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 5
    rule_ids = [r["rule_id"] for r in rules]
    assert "RULE_DATA_DEFICIENCY" in rule_ids
    assert "RULE_HIGH_AMOUNT_INR" in rule_ids

    # Get single rule
    res_single = client.get("/api/expert-system/rules/RULE_DATA_DEFICIENCY")
    assert res_single.status_code == 200
    assert res_single.json()["name"] == "Missing Counterparty Reference"

    # Missing rule 404
    res_404 = client.get("/api/expert-system/rules/NONEXISTENT_RULE_ID")
    assert res_404.status_code == 404

def test_api_evaluate_direct_facts(client):
    """Test POST /api/expert-system/evaluate with custom fact payload."""
    payload = {
        "facts": [
            {"name": "currency", "value": "INR"},
            {"name": "amount", "value": 350000},
            {"name": "hour_of_day", "value": 3},  # Off-hours
            {"name": "channel", "value": "ONLINE"},
        ]
    }
    response = client.post("/api/expert-system/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_cycles"] >= 2
    # Late night high value should trigger
    act_ids = [a["rule_id"] for a in data["activated_rules"]]
    assert "RULE_HIGH_AMOUNT_INR" in act_ids
    assert "RULE_LATE_NIGHT_HIGH_VALUE" in act_ids
    assert data["final_recommendation"] == "HUMAN_SUPERVISORY_REVIEW"

def test_transaction_assessment_workflow(client):
    """
    Test full end-to-end transaction assessment:
    1. Create transaction in database
    2. Call POST /api/transactions/{id}/assess
    3. Verify assessment persistence and retrieval
    """
    # Create test transaction (High amount off-hours)
    create_res = client.post("/api/transactions", json={
        "reference": "TXN-ASSESS-001",
        "timestamp": "2026-10-21T03:30:00Z",  # 3:30 AM
        "amount": 450000.0,
        "currency": "INR",
        "sender_reference": "USR-VIP-101",
        "receiver_reference": "MERCH-GOLD-01",
        "transaction_type": "TRANSFER",
        "channel": "MOBILE_APP",
        "status": "COMPLETED",
    })
    assert create_res.status_code == 201
    txn_id = create_res.json()["id"]

    # Assess transaction
    assess_res = client.post(f"/api/transactions/{txn_id}/assess")
    assert assess_res.status_code == 200
    assessment = assess_res.json()
    assert assessment["transaction_id"] == txn_id
    assert assessment["transaction_reference"] == "TXN-ASSESS-001"
    assert assessment["rules_triggered_count"] >= 2
    assert assessment["final_recommendation"] == "HUMAN_SUPERVISORY_REVIEW"
    assert assessment["overall_severity"] == "HIGH"
    assert "reasoning chain" in assessment["trace"]["human_readable_summary"].lower()

    # Query assessment history
    history_res = client.get(f"/api/transactions/{txn_id}/assessments")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["assessment_id"] == assessment["assessment_id"]

    # Query assessment by assessment_id
    assess_id = assessment["assessment_id"]
    get_res = client.get(f"/api/assessments/{assess_id}")
    assert get_res.status_code == 200
    assert get_res.json()["assessment_id"] == assess_id

def test_assess_nonexistent_transaction_404(client):
    """Assessing a non-existent transaction must return 404."""
    res = client.post("/api/transactions/999999/assess")
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]
