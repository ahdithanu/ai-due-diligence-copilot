import pytest
from backend.domain.schemas import (
    DiligenceState,
    EvidenceRecord,
    FinancialMetricRecord,
    ClaimNode,
    ClaimType,
    MaterialityLevel,
    SpecialistAnalysis
)
from backend.nodes.financial_analyst_node import (
    DeterministicFinancialEngineNode,
    FinancialAnalystNode
)
from backend.nodes.financial_critic_node import FinancialCriticNode

@pytest.mark.asyncio
async def test_deterministic_financial_engine_node():
    state = DiligenceState(
        investment_id="inv_engine",
        company_name="Acme Financials",
        industry="Fintech",
        target_round="Series B"
    )
    ev = EvidenceRecord(
        document_id="doc1",
        chunk_id="chk1",
        content="MRR is $50K in FY2024.",
        claim_type=ClaimType.FACT
    )
    state.evidence_records.append(ev)

    engine_node = DeterministicFinancialEngineNode()
    updated_state = await engine_node.execute(state)

    assert len(updated_state.financial_metrics) >= 1
    arr_metric = next((m for m in updated_state.financial_metrics if m.metric_name == "ARR"), None)
    assert arr_metric is not None
    assert arr_metric.value == 600000.0
    assert arr_metric.is_deterministic is True

    # Run again to verify deduplication
    state_run2 = await engine_node.execute(updated_state)
    arr_metrics_count = sum(1 for m in state_run2.financial_metrics if m.metric_name == "ARR")
    assert arr_metrics_count == 1


@pytest.mark.asyncio
async def test_financial_analyst_node():
    state = DiligenceState(
        investment_id="inv_analyst",
        company_name="SaaS Corp",
        industry="Enterprise Software",
        target_round="Series A"
    )
    ev = EvidenceRecord(
        id="ev_001",
        document_id="doc1",
        chunk_id="chk1",
        content="MRR is $100K in FY2024.",
        claim_type=ClaimType.FACT
    )
    fm = FinancialMetricRecord(
        metric_name="ARR",
        value=1200000.0,
        unit="USD",
        period="FY2024",
        formula="MRR * 12",
        input_evidence_ids=["ev_001"]
    )
    state.evidence_records.append(ev)
    state.financial_metrics.append(fm)

    analyst_node = FinancialAnalystNode()
    updated_state = await analyst_node.execute(state)

    analysis = updated_state.specialist_analyses.get("Financial")
    assert analysis is not None
    assert analysis.domain == "Financial"
    assert len(analysis.claims) >= 1
    assert any(c.evidence_ids == ["ev_001"] for c in analysis.claims)
    assert analysis.confidence_score > 0.0


@pytest.mark.asyncio
async def test_financial_critic_node_pass_case():
    state = DiligenceState(
        investment_id="inv_critic_pass",
        company_name="Good Metrics Inc",
        industry="SaaS",
        target_round="Series A"
    )
    ev = EvidenceRecord(
        id="ev_valid_1",
        document_id="doc1",
        chunk_id="chk1",
        content="MRR is $100K in FY2024.",
        claim_type=ClaimType.FACT
    )
    fm = FinancialMetricRecord(
        metric_name="ARR",
        value=1200000.0,
        unit="USD",
        period="FY2024",
        formula="MRR * 12",
        input_evidence_ids=["ev_valid_1"]
    )
    state.evidence_records.append(ev)
    state.financial_metrics.append(fm)

    analysis = SpecialistAnalysis(
        domain="Financial",
        summary="Analysis for Good Metrics Inc",
        claims=[
            ClaimNode(
                text="ARR for FY2024 is calculated at 1200000.0 USD.",
                claim_type=ClaimType.CALCULATION,
                evidence_ids=["ev_valid_1"],
                materiality=MaterialityLevel.HIGH
            )
        ]
    )
    state.specialist_analyses["Financial"] = analysis

    critic_node = FinancialCriticNode()
    updated_state = await critic_node.execute(state)

    eval_result = updated_state.evaluations[-1]
    assert eval_result.overall_pass is True
    assert eval_result.financial_correctness_score == 1.0
    assert eval_result.citation_correctness_score == 1.0
    assert analysis.passed_evaluation is True


@pytest.mark.asyncio
async def test_financial_critic_node_tolerance_and_citation_failures():
    state = DiligenceState(
        investment_id="inv_critic_fail",
        company_name="Bad Claims Inc",
        industry="SaaS",
        target_round="Series A"
    )
    ev = EvidenceRecord(
        id="ev_valid_1",
        document_id="doc1",
        chunk_id="chk1",
        content="MRR is $100K in FY2024.",
        claim_type=ClaimType.FACT
    )
    fm = FinancialMetricRecord(
        metric_name="ARR",
        value=1200000.0,
        unit="USD",
        period="FY2024",
        formula="MRR * 12",
        input_evidence_ids=["ev_valid_1"]
    )
    state.evidence_records.append(ev)
    state.financial_metrics.append(fm)

    # Claim 1: Incorrect value (differs by >0.01%)
    # Claim 2: Invalid evidence ID
    analysis = SpecialistAnalysis(
        domain="Financial",
        summary="Faulty analysis",
        claims=[
            ClaimNode(
                text="ARR for FY2024 is calculated at 1500000.0 USD.",  # Wrong value: 1.5M vs 1.2M
                claim_type=ClaimType.CALCULATION,
                evidence_ids=["ev_valid_1"],
                materiality=MaterialityLevel.HIGH
            ),
            ClaimNode(
                text="Some claim with fake citation",
                claim_type=ClaimType.FACT,
                evidence_ids=["fake_ev_id_999"],  # Invalid citation
                materiality=MaterialityLevel.MEDIUM
            )
        ]
    )
    state.specialist_analyses["Financial"] = analysis

    critic_node = FinancialCriticNode()
    updated_state = await critic_node.execute(state)

    eval_result = updated_state.evaluations[-1]
    assert eval_result.overall_pass is False
    assert eval_result.financial_correctness_score < 1.0
    assert eval_result.citation_correctness_score < 1.0
    assert len(eval_result.critique_feedback) >= 2
    assert analysis.passed_evaluation is False
