import io
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.domain.schemas import DiligenceStatus, MaterialityLevel

@pytest.mark.asyncio
async def test_full_17_node_e2e_diligence_pipeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Prospective Investment
        create_payload = {
            "company_name": "Horizon Semiconductor AI",
            "industry": "DeepTech / AI Hardware",
            "target_round": "Series B",
            "check_size_usd": 10000000.0
        }
        create_resp = await client.post("/api/v1/investments", json=create_payload)
        assert create_resp.status_code == 201
        inv_data = create_resp.json()
        inv_id = inv_data["investment_id"]
        assert inv_data["company_name"] == "Horizon Semiconductor AI"

        # 2. Upload Diligence Material Document
        doc_content = (
            b"Horizon Semiconductor AI Pitch Deck & Financial Summary\n"
            b"Overview: Horizon is building next-generation photonic AI accelerators.\n"
            b"Market: TAM is $80B growing at 35% CAGR driven by hyperscaler AI cluster demand.\n"
            b"Financials: FY2024 ARR reached $12M with 82% Gross Margin and 130% Net Revenue Retention.\n"
            b"Unit Economics: LTV/CAC ratio is 4.5x with 8 months CAC Payback period.\n"
            b"Moat: 8 core patents granted on optical matrix multiplication.\n"
            b"Risks: Key person reliance on CEO. Lead times on TSMC foundry allocation."
        )
        files = {"file": ("horizon_deck.txt", io.BytesIO(doc_content), "text/plain")}
        data = {"doc_type": "PITCH_DECK"}

        upload_resp = await client.post(f"/api/v1/investments/{inv_id}/documents", files=files, data=data)
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["chunks_extracted"] > 0
        assert upload_data["evidence_extracted"] > 0

        # 3. Start Full 17-Node Graph Execution
        start_resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/start")
        assert start_resp.status_code == 200
        final_state = start_resp.json()

        # 4. Verify Final State Output
        assert final_state["investment_id"] == inv_id
        assert len(final_state["financial_metrics"]) > 0
        assert "Financial" in final_state["specialist_analyses"]
        assert "Market" in final_state["specialist_analyses"]
        assert "Competitive" in final_state["specialist_analyses"]
        assert "Customer" in final_state["specialist_analyses"]
        assert "Product" in final_state["specialist_analyses"]
        assert "Risk" in final_state["specialist_analyses"]
        assert "UnitEconomics" in final_state["specialist_analyses"]
        assert len(final_state["risk_register"]) > 0
        assert final_state["bull_case"] is not None
        assert final_state["bear_case"] is not None
        assert final_state["skeptic_critique"] is not None
        assert final_state["investment_thesis"] is not None
        assert final_state["recommendation"] in ["INVEST", "PASS", "CONDITIONAL_PASS"]
        assert final_state["confidence_score"] is not None
        assert final_state["memo_markdown"] is not None

        # 5. Fetch Generated Memo via REST API
        memo_resp = await client.get(f"/api/v1/investments/{inv_id}/memo")
        assert memo_resp.status_code == 200
        memo_data = memo_resp.json()
        assert memo_data["investment_id"] == inv_id
        assert "Executive Summary" in memo_data["memo_markdown"]
        assert "Horizon Semiconductor AI" in memo_data["memo_markdown"]

        # 6. Fetch Execution Logs
        logs_resp = await client.get(f"/api/v1/investments/{inv_id}/diligence/logs")
        assert logs_resp.status_code == 200
        logs_list = logs_resp.json()
        executed_node_names = [log["node_name"] for log in logs_list]
        assert "DeterministicFinancialEngine" in executed_node_names
        assert "FinancialAnalyst" in executed_node_names
        assert "MarketAnalyst" in executed_node_names
        assert "MemoGenerator" in executed_node_names
