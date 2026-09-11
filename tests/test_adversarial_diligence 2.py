import pytest
from backend.domain.schemas import (
    DiligenceState, DiligenceStatus, DocumentChunk, EvidenceRecord,
    ClaimType, ClaimNode, MaterialityLevel, SpecialistAnalysis, AgentEvaluationResult
)
from backend.nodes.cross_examiner_node import CrossExaminerNode
from backend.nodes.gap_detector_node import GapDetectorNode
from backend.nodes.financial_critic_node import FinancialCriticNode
from backend.nodes.human_review_node import HumanReviewGateNode
from backend.nodes.ic_nodes import SkepticNode
from backend.engine.analyst_critic_loop import AnalystGeneratorNode, CriticEvaluatorNode, analyst_critic_judge_condition

@pytest.mark.asyncio
async def test_adversarial_contradictory_financial_documents():
    """Adversarial Test 1: Pitch deck claims $15M ARR, but audited financials show $4M ARR."""
    state = DiligenceState(
        investment_id="adv_001",
        company_name="Adversarial Corp",
        industry="Enterprise Tech",
        target_round="Series B"
    )
    
    deck_ev = EvidenceRecord(
        document_id="doc_deck",
        chunk_id="c_deck",
        content="Pitch Deck: FY2024 ARR reached $15M with rapid enterprise adoption.",
        claim_type=ClaimType.FACT
    )
    audited_ev = EvidenceRecord(
        document_id="doc_audit",
        chunk_id="c_audit",
        content="Audited P&L: FY2024 total recognized ARR is $4M.",
        claim_type=ClaimType.FACT
    )
    state.evidence_records.extend([deck_ev, audited_ev])

    # Run CrossExaminerNode
    cross_node = CrossExaminerNode()
    state = await cross_node.execute(state)

    assert len(state.contradictions) > 0
    assert any("15M" in c.description or "4M" in c.description for c in state.contradictions)

    # Run HumanReviewGateNode - should flag for human review due to critical financial contradiction
    human_node = HumanReviewGateNode()
    state = await human_node.execute(state)

    assert state.human_review_required is True
    assert state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("contradiction" in r.lower() for r in state.human_review_reasons)

@pytest.mark.asyncio
async def test_adversarial_missing_critical_financial_periods():
    """Adversarial Test 2: Missing financial periods triggers high-priority diligence question."""
    state = DiligenceState(
        investment_id="adv_002",
        company_name="Gap Tech",
        industry="SaaS",
        target_round="Series A"
    )
    # Only Q1 data provided, Q2-Q4 missing
    q1_ev = EvidenceRecord(
        document_id="doc_q1",
        chunk_id="c_q1",
        content="Q1 2024 Revenue was $500K.",
        claim_type=ClaimType.FACT
    )
    state.evidence_records.append(q1_ev)

    gap_node = GapDetectorNode()
    state = await gap_node.execute(state)

    assert len(state.open_questions) > 0
    # Top priority question should address missing periods
    top_q = state.open_questions[0]
    assert top_q.priority in [1, 2]
    assert top_q.materiality in [MaterialityLevel.CRITICAL, MaterialityLevel.HIGH]


@pytest.mark.asyncio
async def test_adversarial_unsupported_financial_claims():
    """Adversarial Test 3: Analyst produces financial claim with incorrect math or bad citation."""
    state = DiligenceState(
        investment_id="adv_003",
        company_name="Math Fail Inc",
        industry="FinTech",
        target_round="Seed"
    )
    
    # Financial analysis with fake numbers not supported by evidence
    state.specialist_analyses["Financial"] = SpecialistAnalysis(
        domain="Financial",
        summary="Company has 99% gross margin and $50M ARR.",
        claims=[
            ClaimNode(
                text="ARR reached $50M in FY2024.",
                claim_type=ClaimType.CALCULATION,
                evidence_ids=["fake_ev_id"],
                materiality=MaterialityLevel.CRITICAL
            )
        ],
        confidence_score=0.9
    )

    critic_node = FinancialCriticNode()
    state = await critic_node.execute(state)

    analysis = state.specialist_analyses["Financial"]
    assert analysis.passed_evaluation is False
    assert len(state.evaluations) > 0
    latest_eval = state.evaluations[-1]
    assert latest_eval.overall_pass is False

@pytest.mark.asyncio
async def test_adversarial_max_iteration_loop_termination():
    """Adversarial Test 4: Analyst loop fails evaluation 3 times, triggering max iteration fallback."""
    state = DiligenceState(
        investment_id="adv_004",
        company_name="Looping Corp",
        industry="AI",
        target_round="Seed"
    )

    # Set iteration count to 3
    state.iteration_counts["TestDomain"] = 3
    state.specialist_analyses["TestDomain"] = SpecialistAnalysis(
        domain="TestDomain",
        summary="Unsubstantiated claims",
        confidence_score=0.4,
        iteration_count=3,
        passed_evaluation=False
    )
    eval_result = AgentEvaluationResult(
        evaluator_name="TestEvaluator",
        target_node="TestDomain",
        overall_pass=False,
        critique_feedback=["Persistent ungrounded claims"]
    )
    state.evaluations.append(eval_result)

    # Check routing condition
    next_edge = analyst_critic_judge_condition(state, "TestDomain")
    assert next_edge == "max_iterations_reached"

    # Human review gate handles max iterations
    human_node = HumanReviewGateNode()
    state = await human_node.execute(state)
    assert state.human_review_required is True
    assert state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("max iteration" in r.lower() for r in state.human_review_reasons)


