import pytest
import uuid
from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    EvidenceRecord,
    FinancialMetricRecord,
    SpecialistAnalysis,
    ClaimNode,
    ClaimType,
    MaterialityLevel,
    ContradictionRecord,
    DiligenceQuestion
)
from backend.nodes.ic_nodes import (
    BullNode,
    BearNode,
    SkepticNode,
    ICSynthesizerNode,
    skeptic_routing_condition
)


@pytest.mark.asyncio
async def test_bull_node():
    ev1 = EvidenceRecord(
        id="ev_001",
        document_id="doc_1",
        chunk_id="chk_1",
        content="Company ARR grew by 150% YoY to reach $10M.",
        claim_type=ClaimType.FACT
    )
    fm1 = FinancialMetricRecord(
        metric_name="Revenue_Growth",
        value=150.0,
        unit="percentage",
        period="FY2024",
        formula="YoY Growth",
        input_evidence_ids=["ev_001"]
    )
    sa = SpecialistAnalysis(
        domain="Market",
        summary="Strong market demand.",
        strengths=["Defensible market moat in enterprise SaaS"],
        confidence_score=0.9
    )

    state = DiligenceState(
        investment_id="inv_100",
        company_name="Acme AI",
        industry="Enterprise AI",
        target_round="Series A",
        evidence_records=[ev1],
        financial_metrics=[fm1],
        specialist_analyses={"Market": sa}
    )

    bull_node = BullNode()
    res_state = await bull_node.process(state)

    assert res_state.bull_case is not None
    assert "Acme AI" in res_state.bull_case
    assert "[Evidence: ev_001]" in res_state.bull_case
    assert res_state.status == DiligenceStatus.INVESTMENT_COMMITTEE


@pytest.mark.asyncio
async def test_bear_node():
    ev1 = EvidenceRecord(
        id="ev_002",
        document_id="doc_1",
        chunk_id="chk_2",
        content="Monthly burn rate increased to $350k with 6 months of runway remaining.",
        claim_type=ClaimType.FACT
    )
    risk_claim = ClaimNode(
        text="High burn rate and short runway elevate refinancing risk",
        claim_type=ClaimType.INFERENCE,
        materiality=MaterialityLevel.HIGH,
        evidence_ids=["ev_002"]
    )
    fm_burn = FinancialMetricRecord(
        metric_name="Burn_Rate",
        value=350000.0,
        unit="USD/month",
        period="Q4_2024",
        formula="Monthly cash out",
        input_evidence_ids=["ev_002"]
    )

    state = DiligenceState(
        investment_id="inv_101",
        company_name="Acme AI",
        industry="Enterprise AI",
        target_round="Series A",
        evidence_records=[ev1],
        risk_register=[risk_claim],
        financial_metrics=[fm_burn]
    )

    bear_node = BearNode()
    res_state = await bear_node.process(state)

    assert res_state.bear_case is not None
    assert "Refinancing Risk" in res_state.bear_case or "Burn_Rate" in res_state.bear_case or "Risk Factor" in res_state.bear_case
    assert "[Evidence: ev_002]" in res_state.bear_case
    assert res_state.status == DiligenceStatus.INVESTMENT_COMMITTEE


@pytest.mark.asyncio
async def test_skeptic_node():
    # Setup state with unresolved critical contradiction
    contradiction = ContradictionRecord(
        claim_a_id="claim_1",
        claim_b_id="claim_2",
        description="Pitch deck claims $10M ARR while audited statements show $5M ARR.",
        materiality=MaterialityLevel.CRITICAL,
        status="OPEN"
    )

    state = DiligenceState(
        investment_id="inv_102",
        company_name="Acme AI",
        industry="Enterprise AI",
        target_round="Series A",
        bull_case="Acme AI has incredible upside claims without evidence.",
        contradictions=[contradiction]
    )

    skeptic_node = SkepticNode()
    res_state = await skeptic_node.process(state)

    assert res_state.skeptic_critique is not None
    assert "Skeptic Critique" in res_state.skeptic_critique
    assert res_state.human_review_required is True
    assert any("critical contradiction" in r.lower() for r in res_state.human_review_reasons)
    assert res_state.status == DiligenceStatus.INVESTMENT_COMMITTEE


@pytest.mark.asyncio
async def test_ic_synthesizer_node():
    ev = EvidenceRecord(id="ev_010", document_id="doc1", chunk_id="c1", content="Solid organic growth.")
    state = DiligenceState(
        investment_id="inv_103",
        company_name="Acme AI",
        industry="Enterprise AI",
        target_round="Series A",
        bull_case="Strong market traction [Evidence: ev_010].",
        bear_case="Early stage execution risk.",
        evidence_records=[ev]
    )

    ic_synth = ICSynthesizerNode()
    res_state = await ic_synth.process(state)

    assert res_state.investment_thesis is not None
    assert res_state.recommendation in ["INVEST", "PASS", "CONDITIONAL_PASS"]
    assert res_state.confidence_score is not None
    assert 0.0 <= res_state.confidence_score <= 1.0
    assert res_state.status == DiligenceStatus.INVESTMENT_COMMITTEE


def test_skeptic_routing_condition():
    # Clean state -> ICSynthesizer
    clean_state = DiligenceState(
        investment_id="inv_clean",
        company_name="Clean Co",
        industry="SaaS",
        target_round="Seed"
    )
    assert skeptic_routing_condition(clean_state) == "ICSynthesizer"

    # State requiring human review -> GapDetector
    flagged_state = DiligenceState(
        investment_id="inv_flagged",
        company_name="Flagged Co",
        industry="SaaS",
        target_round="Seed",
        human_review_required=True
    )
    assert skeptic_routing_condition(flagged_state) == "GapDetector"

    # State with open critical question -> GapDetector
    q_state = DiligenceState(
        investment_id="inv_q",
        company_name="Question Co",
        industry="SaaS",
        target_round="Seed",
        open_questions=[
            DiligenceQuestion(
                question="Where are the audited financials?",
                reason_it_matters="Financial audit required",
                related_risk_or_thesis="Fraud risk",
                required_evidence="Audited statements",
                materiality=MaterialityLevel.CRITICAL,
                status="OPEN"
            )
        ]
    )
    assert skeptic_routing_condition(q_state) == "GapDetector"
