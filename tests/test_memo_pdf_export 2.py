import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.database import AsyncSessionLocal
from backend.domain.schemas import DiligenceState, DiligenceStatus, EvidenceRecord, ClaimType
from backend.services.memo_generator import (
    generate_investment_memo,
    generate_investment_memo_pdf
)
from backend.nodes.memo_generator_node import MemoGeneratorNode


def test_generate_investment_memo_pdf_valid_header():
    sample_memo = (
        "# Investment Due Diligence Memo: Horizon Bio\n"
        "**Company**: Horizon Bio | **Industry**: Biotech | **Target Round**: Series B | **Check Size**: $5,000,000.00 | **Date**: 2026-08-11\n"
        "**Status**: IC_APPROVED\n\n"
        "## Executive Summary\n\n"
        "Horizon Bio demonstrates strong initial Phase II clinical trial data [Evidence: ev_bio_101].\n\n"
        "## Financial Analysis\n\n"
        "| Metric | Value | Unit | Period | Citations |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| Run Rate | 15.5 | M USD | FY2025 | [Evidence: ev_bio_101] |\n\n"
        "## Recommendation\n\n"
        "**INVEST**"
    )

    pdf_bytes = generate_investment_memo_pdf(sample_memo, "Horizon Bio")

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_memo_download_endpoints():
    async with AsyncSessionLocal() as db_session:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Create Investment
            create_resp = await client.post(
                "/api/v1/investments",
                json={
                    "company_name": "Horizon Bio",
                    "industry": "Biotech",
                    "target_round": "Series B",
                    "check_size_usd": 5000000.0
                }
            )
            assert create_resp.status_code == 201
            inv_id = create_resp.json()["investment_id"]

            # 2. Process Diligence State with MemoGeneratorNode
            state = DiligenceState(
                investment_id=inv_id,
                company_name="Horizon Bio",
                industry="Biotech",
                target_round="Series B",
                check_size_usd=5000000.0,
                status=DiligenceStatus.MEMO_GENERATED,
                recommendation="INVEST",
                confidence_score=0.91,
                evidence_records=[
                    EvidenceRecord(
                        id="ev_bio_101",
                        document_id="doc_trial",
                        chunk_id="chk_0",
                        content="Phase II trial met primary endpoints with p < 0.01.",
                        claim_type=ClaimType.FACT
                    )
                ]
            )
            node = MemoGeneratorNode(db_session=db_session)
            await node.process(state)

            # 3. Download PDF Memo
            pdf_resp = await client.get(f"/api/v1/investments/{inv_id}/memo/download?format=pdf")
            assert pdf_resp.status_code == 200
            assert "application/pdf" in pdf_resp.headers["content-type"]
            assert "Horizon_Bio_Investment_Memo.pdf" in pdf_resp.headers["content-disposition"]
            assert pdf_resp.content.startswith(b"%PDF-")

            # 4. Download Markdown Memo
            md_resp = await client.get(f"/api/v1/investments/{inv_id}/memo/download?format=markdown")
            assert md_resp.status_code == 200
            assert "text/markdown" in md_resp.headers["content-type"]
            assert "Horizon_Bio_Investment_Memo.md" in md_resp.headers["content-disposition"]
            assert "Investment Due Diligence Memo: Horizon Bio" in md_resp.text
            assert "[Evidence: ev_bio_101]" in md_resp.text

            # 5. Invalid Format Query Param -> 400
            err_fmt_resp = await client.get(f"/api/v1/investments/{inv_id}/memo/download?format=docx")
            assert err_fmt_resp.status_code == 400

            # 6. Non-existent Investment ID -> 404
            err_404_resp = await client.get("/api/v1/investments/inv_non_existent/memo/download?format=pdf")
            assert err_404_resp.status_code == 404
