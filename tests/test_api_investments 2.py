import io
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_create_and_list_investment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create Investment
        create_payload = {
            "company_name": "Starlight Robotics",
            "industry": "DeepTech / Robotics",
            "target_round": "Series A",
            "check_size_usd": 3000000.0
        }
        resp = await client.post("/api/v1/investments", json=create_payload)
        assert resp.status_code == 201
        data = resp.json()
        inv_id = data["investment_id"]
        assert data["company_name"] == "Starlight Robotics"
        assert data["status"] == "CREATED"

        # List Investments
        list_resp = await client.get("/api/v1/investments")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert any(i["investment_id"] == inv_id for i in list_data)

        # Get Workspace State
        get_resp = await client.get(f"/api/v1/investments/{inv_id}")
        assert get_resp.status_code == 200
        state = get_resp.json()
        assert state["investment_id"] == inv_id
        assert state["company_name"] == "Starlight Robotics"

@pytest.mark.asyncio
async def test_document_upload_and_evidence():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create Investment
        create_payload = {
            "company_name": "Nexus Quantum",
            "industry": "Quantum Computing",
            "target_round": "Seed",
            "check_size_usd": 1500000.0
        }
        create_resp = await client.post("/api/v1/investments", json=create_payload)
        inv_id = create_resp.json()["investment_id"]

        # Upload Sample Deck Text File
        file_content = b"Nexus Quantum Pitch Deck\nARR is $2.5M in FY2024 with 140% NRR.\nGross Margin reached 78% across 45 enterprise clients."
        files = {"file": ("deck.txt", io.BytesIO(file_content), "text/plain")}
        data = {"doc_type": "PITCH_DECK"}

        upload_resp = await client.post(f"/api/v1/investments/{inv_id}/documents", files=files, data=data)
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["chunks_extracted"] > 0
        assert upload_data["evidence_extracted"] > 0
        assert upload_data["status"] == "EVIDENCE_EXTRACTED"

        # Fetch Evidence
        evidence_resp = await client.get(f"/api/v1/investments/{inv_id}/evidence")
        assert evidence_resp.status_code == 200
        evidence_list = evidence_resp.json()
        assert len(evidence_list) > 0
        assert any("ARR" in ev["content"] or "Gross Margin" in ev["content"] for ev in evidence_list)

        # Fetch Financials
        fin_resp = await client.get(f"/api/v1/investments/{inv_id}/financials")
        assert fin_resp.status_code == 200
        assert isinstance(fin_resp.json(), list)

