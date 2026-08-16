import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.domain.schemas import (
    CapTableEntry, DiligenceState, DiligenceStatus, EvidenceRecord, ClaimType,
    ChatMessage, DataRoomRequest, ICAudioScript
)
from backend.services.waterfall_calculator import calculate_exit_waterfall
from backend.services.sensitivity_engine import run_sensitivity_stress_test
from backend.services.diligence_chat_service import process_diligence_chat
from backend.services.audio_ic_service import generate_ic_audio_script
from backend.services.teaser_generator import generate_investment_teaser


def test_waterfall_calculation_participating_and_moic():
    cap_table = [
        CapTableEntry(
            share_class="Series A Preferred",
            investor_name="Alpha VC",
            shares_held=2000000.0,
            ownership_pct=20.0,
            liquidation_preference_multiplier=1.0,
            is_participating=True,
            cap_multiplier=2.0
        ),
        CapTableEntry(
            share_class="Common",
            investor_name="Founders",
            shares_held=8000000.0,
            ownership_pct=80.0,
            liquidation_preference_multiplier=0.0,
            is_participating=False
        )
    ]
    
    scenario = calculate_exit_waterfall(
        cap_table=cap_table,
        exit_valuation_usd=20000000.0,
        total_investment_usd=5000000.0
    )
    
    assert scenario.exit_valuation_usd == 20000000.0
    assert len(scenario.payouts) == 2
    
    alpha_payout = next(p for p in scenario.payouts if p.investor_name == "Alpha VC")
    founder_payout = next(p for p in scenario.payouts if p.investor_name == "Founders")
    
    assert alpha_payout.payout_usd > 5000000.0  # Pref + participation
    assert alpha_payout.moic > 1.0
    assert founder_payout.payout_usd > 0.0


def test_sensitivity_stress_testing_matrix():
    metrics = {
        "runway_months": 18.0,
        "ebitda_margin_pct": -12.0,
        "cac_payback_months": 10.0
    }
    
    matrix = run_sensitivity_stress_test(metrics)
    assert matrix.base_runway_months == 18.0
    assert matrix.base_ebitda_margin_pct == -12.0
    assert len(matrix.scenarios) == 5
    
    scenario_names = [s.scenario_name for s in matrix.scenarios]
    assert "Base Case" in scenario_names
    assert "Moderate Growth Miss" in scenario_names
    assert "Churn Spike" in scenario_names
    assert "Severe Macro Downturn" in scenario_names
    assert "Optimistic Upside" in scenario_names
    
    severe = next(s for s in matrix.scenarios if s.scenario_name == "Severe Macro Downturn")
    assert severe.risk_level == "CRITICAL"
    assert severe.resulting_runway_months < matrix.base_runway_months


def test_chat_qa_and_data_room_request_generation():
    state = DiligenceState(
        investment_id="inv-test-chat",
        company_name="Apex Cyber",
        industry="Cybersecurity",
        target_round="Series B",
        check_size_usd=10000000.0,
        status=DiligenceStatus.EVIDENCE_EXTRACTED
    )
    
    # Add evidence record
    state.evidence_records.append(
        EvidenceRecord(
            document_id="doc-1",
            chunk_id="chunk-1",
            content="Apex Cyber reported ARR of $12.5M in Q4 2024 with 132% NRR.",
            page_number=3,
            section_title="Financial Overview",
            claim_type=ClaimType.FACT
        )
    )
    
    # Ask about ARR and financials
    question = "What is the audited ARR growth and monthly P&L burn?"
    assistant_msg, new_requests = process_diligence_chat(state, question)
    
    assert isinstance(assistant_msg, ChatMessage)
    assert assistant_msg.role == "assistant"
    assert len(assistant_msg.evidence_citations) > 0
    assert "Apex Cyber" in assistant_msg.content
    
    assert len(new_requests) > 0
    assert any("audited" in r.document_needed.lower() or "financial" in r.document_needed.lower() for r in new_requests)


def test_ic_audio_script_generation():
    state = DiligenceState(
        investment_id="inv-test-audio",
        company_name="Vanguard AI",
        industry="AI Infrastructure",
        target_round="Series A",
        check_size_usd=5000000.0,
        bull_case="Strong technical moat with 3x faster inference speeds.",
        bear_case="High cloud compute costs eating gross margins."
    )
    
    script = generate_ic_audio_script(state)
    assert isinstance(script, ICAudioScript)
    assert "Vanguard AI" in script.title
    assert len(script.speakers) == 3
    
    speaker_roles = [s["role"] for s in script.speakers]
    assert "Bull Partner" in speaker_roles
    assert "Bear Partner" in speaker_roles
    assert any("Skeptic" in r or "Chair" in r for r in speaker_roles)
    
    assert len(script.transcript_lines) >= 6
    assert any("Vanguard AI" in line["text"] for line in script.transcript_lines)


def test_teaser_generator():
    state = DiligenceState(
        investment_id="inv-test-teaser",
        company_name="Helios Energy",
        industry="CleanTech / Solar",
        target_round="Series A",
        check_size_usd=4000000.0,
        recommendation="INVEST",
        confidence_score=0.92
    )
    
    teaser = generate_investment_teaser(state)
    assert "teaser_markdown" in teaser
    assert "teaser_html" in teaser
    assert teaser["company_name"] == "Helios Energy"
    
    md_content = teaser["teaser_markdown"]
    assert "Helios Energy" in md_content
    assert "INSTITUTIONAL INVESTMENT TEASER" in md_content
    assert "INVEST" in md_content
    
    html_content = teaser["teaser_html"]
    assert "<html>" in html_content
    assert "Helios Energy" in html_content


@pytest.mark.asyncio
async def test_institutional_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create an investment first
        create_resp = await client.post("/api/v1/investments", json={
            "company_name": "Horizon Robotics",
            "industry": "Robotics & AI",
            "target_round": "Series A",
            "check_size_usd": 5000000.0
        })
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investment_id"]

        # 2. Test Waterfall endpoint
        waterfall_resp = await client.post(f"/api/v1/investments/{inv_id}/waterfall", json={
            "exit_valuation_usd": 40000000.0,
            "total_investment_usd": 8000000.0
        })
        assert waterfall_resp.status_code == 200
        wf_data = waterfall_resp.json()
        assert wf_data["exit_valuation_usd"] == 40000000.0
        assert len(wf_data["payouts"]) >= 2

        # 3. Test Sensitivity endpoint
        sensitivity_resp = await client.post(f"/api/v1/investments/{inv_id}/sensitivity", json={
            "financial_metrics": {"runway_months": 20.0, "ebitda_margin_pct": -10.0}
        })
        assert sensitivity_resp.status_code == 200
        sens_data = sensitivity_resp.json()
        assert sens_data["base_runway_months"] == 20.0
        assert len(sens_data["scenarios"]) == 5

        # 4. Test Chat endpoint
        chat_resp = await client.post(f"/api/v1/investments/{inv_id}/chat", json={
            "question": "What are the key financial risks and audited ARR figures?"
        })
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "message" in chat_data
        assert chat_data["message"]["role"] == "assistant"
        assert len(chat_data["data_room_requests_generated"]) > 0

        # 5. Test Data Room Requests endpoint
        dr_resp = await client.get(f"/api/v1/investments/{inv_id}/data-room-requests")
        assert dr_resp.status_code == 200
        dr_data = dr_resp.json()
        assert len(dr_data) > 0
        assert any("category" in req for req in dr_data)

        # 6. Test IC Audio Script endpoint
        audio_resp = await client.get(f"/api/v1/investments/{inv_id}/ic-audio-script")
        assert audio_resp.status_code == 200
        audio_data = audio_resp.json()
        assert "title" in audio_data
        assert len(audio_data["speakers"]) == 3
        assert len(audio_data["transcript_lines"]) > 0

        # 7. Test Teaser endpoint
        teaser_resp = await client.get(f"/api/v1/investments/{inv_id}/teaser")
        assert teaser_resp.status_code == 200
        teaser_data = teaser_resp.json()
        assert "teaser_markdown" in teaser_data
        assert "teaser_html" in teaser_data
        assert teaser_data["company_name"] == "Horizon Robotics"
