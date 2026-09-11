import pytest
from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    EvidenceRecord,
    FinancialMetricRecord,
    ClaimType,
    MaterialityLevel,
    SpecialistAnalysis
)
from backend.nodes.specialist_nodes import (
    MarketAnalystNode,
    CompetitiveAnalystNode,
    CustomerAnalystNode,
    ProductAnalystNode,
    RiskAnalystNode,
    UnitEconomicsAnalystNode
)


@pytest.fixture
def base_diligence_state() -> DiligenceState:
    state = DiligenceState(
        investment_id="inv_test_specialists",
        company_name="Apex AI Systems",
        industry="Enterprise AI Automation",
        target_round="Series A",
        check_size_usd=5000000.0
    )

    ev1 = EvidenceRecord(
        document_id="doc_deck",
        chunk_id="chunk_1",
        content="Apex AI operates in a $45B TAM growing at 28% CAGR. Industry tailwinds are driven by enterprise automation demand.",
        claim_type=ClaimType.FACT,
        page_number=3,
        section_title="Market Opportunity"
    )

    ev2 = EvidenceRecord(
        document_id="doc_deck",
        chunk_id="chunk_2",
        content="Core competitive moat includes 3 filed patents on workflow orchestration and proprietary model weights.",
        claim_type=ClaimType.FACT,
        page_number=5,
        section_title="Technology & Moat"
    )

    ev3 = EvidenceRecord(
        document_id="doc_financials",
        chunk_id="chunk_3",
        content="Net Revenue Retention (NRR) reached 125% in FY2024. Top customer accounts for 35% of total revenue creating concentration risk.",
        claim_type=ClaimType.FACT,
        page_number=8,
        section_title="Financial Highlights"
    )

    ev4 = EvidenceRecord(
        document_id="doc_risk",
        chunk_id="chunk_4",
        content="Key person reliance on founding CTO. High regulatory compliance exposure under EU AI Act.",
        claim_type=ClaimType.FACT,
        page_number=12,
        section_title="Risk Factors"
    )

    state.evidence_records.extend([ev1, ev2, ev3, ev4])

    # Add sample financial metrics
    fm1 = FinancialMetricRecord(
        metric_name="Net_Revenue_Retention",
        value=125.0,
        unit="percentage",
        period="FY2024",
        formula="NRR calculation",
        input_evidence_ids=[ev3.id]
    )
    fm2 = FinancialMetricRecord(
        metric_name="Customer_Concentration",
        value=35.0,
        unit="percentage",
        period="FY2024",
        formula="Top customer revenue / Total revenue",
        input_evidence_ids=[ev3.id]
    )
    fm3 = FinancialMetricRecord(
        metric_name="LTV_CAC",
        value=4.2,
        unit="ratio",
        period="FY2024",
        formula="LTV / CAC",
        input_evidence_ids=[ev3.id]
    )
    fm4 = FinancialMetricRecord(
        metric_name="CAC_Payback",
        value=9.0,
        unit="months",
        period="FY2024",
        formula="CAC / (ARPU * Gross Margin)",
        input_evidence_ids=[ev3.id]
    )
    fm5 = FinancialMetricRecord(
        metric_name="Runway",
        value=8.0,
        unit="months",
        period="FY2024",
        formula="Cash / Monthly Burn",
        input_evidence_ids=[ev4.id]
    )

    state.financial_metrics.extend([fm1, fm2, fm3, fm4, fm5])
    return state


@pytest.mark.asyncio
async def test_market_analyst_node(base_diligence_state):
    node = MarketAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "Market" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["Market"]
    assert analysis.domain == "Market"
    assert len(analysis.claims) > 0
    assert any("TAM" in c.text or "CAGR" in c.text or "Apex AI" in c.text for c in analysis.claims)
    assert len(analysis.strengths) > 0
    assert updated_state.status == DiligenceStatus.SPECIALIST_DILIGENCE


@pytest.mark.asyncio
async def test_competitive_analyst_node(base_diligence_state):
    node = CompetitiveAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "Competitive" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["Competitive"]
    assert analysis.domain == "Competitive"
    assert len(analysis.claims) > 0
    assert len(analysis.strengths) > 0


@pytest.mark.asyncio
async def test_customer_analyst_node(base_diligence_state):
    node = CustomerAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "Customer" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["Customer"]
    assert analysis.domain == "Customer"
    assert len(analysis.claims) > 0
    assert any("NRR" in c.text or "Concentration" in c.text for c in analysis.claims)


@pytest.mark.asyncio
async def test_product_analyst_node(base_diligence_state):
    node = ProductAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "Product" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["Product"]
    assert analysis.domain == "Product"
    assert len(analysis.claims) > 0


@pytest.mark.asyncio
async def test_risk_analyst_node_populates_risk_register(base_diligence_state):
    initial_risk_count = len(base_diligence_state.risk_register)
    node = RiskAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "Risk" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["Risk"]
    assert analysis.domain == "Risk"
    assert len(analysis.claims) > 0

    # Verify state.risk_register was populated
    assert len(updated_state.risk_register) > initial_risk_count
    assert any("Key person" in r.text or "Runway" in r.text or "risk" in r.text.lower() for r in updated_state.risk_register)


@pytest.mark.asyncio
async def test_unit_economics_analyst_node(base_diligence_state):
    node = UnitEconomicsAnalystNode()
    updated_state = await node.execute(base_diligence_state)

    assert "UnitEconomics" in updated_state.specialist_analyses
    analysis: SpecialistAnalysis = updated_state.specialist_analyses["UnitEconomics"]
    assert analysis.domain == "UnitEconomics"
    assert len(analysis.claims) > 0
    assert any("LTV" in c.text or "CAC" in c.text for c in analysis.claims)
