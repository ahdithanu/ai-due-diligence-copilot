import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.config import settings
from backend.services.document_parser import DocumentParserService
from backend.services.memo_generator import generate_full_ic_pack_markdown, generate_full_ic_pack_pdf
from backend.domain.schemas import DiligenceState, DiligenceStatus


@pytest.mark.asyncio
async def test_llm_settings_get_and_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET settings
        res = await ac.get("/api/v1/settings/llm")
        assert res.status_code == 200
        data = res.json()
        assert "current_provider" in data
        assert "available_providers" in data
        assert "routed" in data["available_providers"]
        assert "gemini" in data["available_providers"]

        # 2. Update to routed
        res2 = await ac.post("/api/v1/settings/llm", json={
            "provider": "routed"
        })
        assert res2.status_code == 200
        assert res2.json()["current_provider"] == "routed"

        # 3. Reject invalid provider
        res3 = await ac.post("/api/v1/settings/llm", json={
            "provider": "non_existent_provider"
        })
        assert res3.status_code == 400

        # Reset back to mock for test isolation
        await ac.post("/api/v1/settings/llm", json={"provider": "mock"})


@pytest.mark.asyncio
async def test_csv_parser_service(tmp_path):
    parser = DocumentParserService()
    csv_file = tmp_path / "financials.csv"
    csv_file.write_text("Year,ARR,Growth,Gross_Margin\n2023,5.0M,120%,75%\n2024,12.4M,148%,78%\n")

    chunks = parser.parse_file(str(csv_file), "doc-test-1")
    assert len(chunks) >= 1
    assert "ARR" in chunks[0].content
    assert "12.4M" in chunks[0].content
    assert chunks[0].document_id == "doc-test-1"


@pytest.mark.asyncio
async def test_full_ic_pack_generation():
    state = DiligenceState(
        investment_id="inv-test-ic-pack",
        company_name="ApexCloud Technologies",
        industry="B2B Enterprise SaaS",
        target_round="Series A",
        check_size_usd=10000000.0,
        status=DiligenceStatus.MEMO_GENERATED,
        confidence_score=0.92,
        investment_thesis="Market-leading automated cloud optimization engine with net expansion."
    )

    # 1. Generate full Markdown IC pack
    md = generate_full_ic_pack_markdown(state)
    assert "# Investment Due Diligence Memo: ApexCloud Technologies" in md
    assert "## Cap Table & Exit Waterfall Simulation" in md
    assert "Series A Proceeds" in md
    assert "## Financial Sensitivity & Runway Stress Test" in md
    assert "## Compliance, Guardrail & Red-Flag Audit" in md

    # 2. Generate full PDF bytes
    pdf_bytes = generate_full_ic_pack_pdf(state)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_ic_pack_download_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create an investment first
        create_res = await ac.post("/api/v1/investments", json={
            "company_name": "NovaScale AI",
            "industry": "Infrastructure",
            "target_round": "Series Seed",
            "check_size_usd": 3000000.0
        })
        assert create_res.status_code == 201
        inv_id = create_res.json()["investment_id"]

        # Download IC Pack as PDF
        pdf_res = await ac.get(f"/api/v1/investments/{inv_id}/ic-pack/download?format=pdf")
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 500

        # Download IC Pack as Markdown
        md_res = await ac.get(f"/api/v1/investments/{inv_id}/ic-pack/download?format=markdown")
        assert md_res.status_code == 200
        assert "Cap Table & Exit Waterfall Simulation" in md_res.text
