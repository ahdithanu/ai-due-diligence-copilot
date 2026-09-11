import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.database import AsyncSessionLocal
from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    EvidenceRecord,
    FinancialMetricRecord,
    SpecialistAnalysis,
    ClaimNode,
    ClaimType,
    MaterialityLevel
)
from backend.services.memo_generator import generate_investment_memo, InvestmentMemoGenerator
from backend.nodes.memo_generator_node import MemoGeneratorNode


def test_memo_rendering_and_citations():
    ev1 = EvidenceRecord(
        id="ev_101",
        document_id="doc_pitch",
        chunk_id="chk_0",
        content="Acme AI achieved $12M ARR in FY2024 with 80% gross margin.",
        claim_type=ClaimType.FACT
    )
    fm1 = FinancialMetricRecord(
        metric_name="ARR",
        value=12.0,
        unit="M USD",
        period="FY2024",
        formula="ARR calculated from active subscriptions",
        input_evidence_ids=["ev_101"]
    )
    product_sa = SpecialistAnalysis(
        domain="Product",
        summary="Enterprise-grade AI copilot platform with patent-pending workflow automation.",
        claims=[
            ClaimNode(
                text="Platform processes 1M tokens/sec with sub-50ms latency",
                claim_type=ClaimType.FACT,
                evidence_ids=["ev_101"]
            )
        ]
    )

    state = DiligenceState(
        investment_id="inv_test_memo",
        company_name="Acme AI",
        industry="Artificial Intelligence",
        target_round="Series A",
        check_size_usd=5000000.0,
        status=DiligenceStatus.INVESTMENT_COMMITTEE,
        evidence_records=[ev1],
        financial_metrics=[fm1],
        specialist_analyses={"Product": product_sa},
        bull_case="Strong revenue growth [Evidence: ev_101].",
        bear_case="High key person dependency.",
        investment_thesis="Acme AI is well positioned to lead enterprise AI due diligence.",
        recommendation="INVEST",
        confidence_score=0.88
    )

    memo_text = generate_investment_memo(state)

    # Verify all 20 required sections exist
    required_sections = [
        "Executive Summary",
        "Company Overview",
        "Investment Thesis",
        "Product",
        "Market",
        "Competition",
        "Business Model",
        "Customers",
        "Growth",
        "Financial Analysis",
        "Unit Economics",
        "Key Strengths",
        "Key Risks",
        "Bull Case",
        "Base Case",
        "Bear Case",
        "Open Diligence Questions",
        "Recommendation",
        "Confidence",
        "Key Evidence"
    ]

    for section in required_sections:
        assert f"## {section}" in memo_text, f"Missing required section: ## {section}"

    # Verify explicit citations formatting
    assert "[Evidence: ev_101]" in memo_text
    assert "Acme AI" in memo_text
    assert "INVEST" in memo_text
    assert "88%" in memo_text


@pytest.mark.asyncio
async def test_memo_generator_node():
    async with AsyncSessionLocal() as db_session:
        state = DiligenceState(
            investment_id="inv_node_test",
            company_name="Node Corp",
            industry="Cloud Infrastructure",
            target_round="Seed",
            recommendation="CONDITIONAL_PASS",
            confidence_score=0.75
        )

        node = MemoGeneratorNode(db_session=db_session)
        res_state = await node.process(state)

        assert res_state.memo_markdown is not None
        assert res_state.status == DiligenceStatus.MEMO_GENERATED
        assert "## Executive Summary" in res_state.memo_markdown


@pytest.mark.asyncio
async def test_memo_api_endpoint():
    async with AsyncSessionLocal() as db_session:
        # 1. Create an investment via API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_resp = await client.post(
                "/api/v1/investments",
                json={
                    "company_name": "API Memo Corp",
                    "industry": "FinTech",
                    "target_round": "Series B",
                    "check_size_usd": 10000000.0
                }
            )
            assert create_resp.status_code == 201
            inv_data = create_resp.json()
            inv_id = inv_data["investment_id"]

            # 2. Test GET memo prior to generation -> 404
            get_404_resp = await client.get(f"/api/v1/investments/{inv_id}/memo")
            assert get_404_resp.status_code == 404

            # 3. Generate memo state and process via node attached to DB
            state = DiligenceState(
                investment_id=inv_id,
                company_name="API Memo Corp",
                industry="FinTech",
                target_round="Series B",
                recommendation="INVEST",
                confidence_score=0.92
            )
            node = MemoGeneratorNode(db_session=db_session)
            await node.process(state)

            # 4. Test GET memo endpoint returning InvestmentMemoResponse
            memo_resp = await client.get(f"/api/v1/investments/{inv_id}/memo")
            assert memo_resp.status_code == 200
            data = memo_resp.json()
            assert data["investment_id"] == inv_id
            assert data["recommendation"] == "INVEST"
            assert data["confidence_score"] == 0.92
            assert "Executive Summary" in data["memo_markdown"]
