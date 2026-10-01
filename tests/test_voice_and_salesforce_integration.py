import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.voice_stream_service import voice_stream_service
from backend.services.salesforce_service import salesforce_service
from backend.domain.schemas import (
    VoiceSimulateTurnRequest,
    AgentforceActionRequest,
    VoiceTurnState
)

client = TestClient(app)


# ==========================================
# Real-Time Voice Streaming Tests
# ==========================================

def test_voice_latency_budget_profile():
    """
    Verify conversational voice latency budget strictly satisfies the sub-700ms threshold.
    """
    profile = voice_stream_service.get_latency_profile()
    
    assert profile.vad_latency_ms <= 120.0
    assert profile.stt_latency_ms <= 200.0
    assert profile.llm_ttft_ms <= 200.0
    assert profile.tts_first_byte_ms <= 150.0
    assert profile.total_e2e_latency_ms <= profile.target_budget_ms
    assert profile.is_within_budget is True


def test_sentence_boundary_chunking():
    """
    Verify text stream is split into synthesized sentences at punctuation marks.
    """
    text = "Apex Cyber reported 12.5M in ARR. The growth rate is 65% year over year! What is the gross churn?"
    chunks = voice_stream_service.chunk_sentences(text)
    
    assert len(chunks) == 3
    assert chunks[0] == "Apex Cyber reported 12.5M in ARR."
    assert chunks[1] == "The growth rate is 65% year over year!"
    assert chunks[2] == "What is the gross churn?"


def test_voice_turn_simulation_normal_and_barge_in():
    """
    Verify voice turn simulation for both uninterrupted speech and mid-turn barge-in.
    """
    # 1. Normal uninterrupted turn
    normal_req = VoiceSimulateTurnRequest(
        user_transcript="What is the audited ARR and customer concentration?",
        simulate_interruption=False
    )
    normal_res = voice_stream_service.simulate_turn(normal_req)
    
    assert normal_res.interrupted is False
    assert normal_res.audio_chunks_count > 1
    assert "12.5 million in ARR" in normal_res.ai_response_text
    assert len(normal_res.timeline_events) >= 5

    # 2. Interrupted turn (user barge-in during AI playback)
    interrupted_req = VoiceSimulateTurnRequest(
        user_transcript="What is the audited ARR and customer concentration?",
        simulate_interruption=True,
        interruption_at_ms=250.0
    )
    interrupted_res = voice_stream_service.simulate_turn(interrupted_req)
    
    assert interrupted_res.interrupted is True
    assert interrupted_res.audio_chunks_count == 1
    assert any("Barge-in event received" in event for event in interrupted_res.timeline_events)
    assert any("discarded remaining sentence buffers" in event for event in interrupted_res.timeline_events)


def test_voice_rest_api_endpoints():
    """
    Test REST endpoints for voice latency profile and simulated turn.
    """
    # GET /api/v1/voice/latency-profile
    resp_profile = client.get("/api/v1/voice/latency-profile")
    assert resp_profile.status_code == 200
    data_profile = resp_profile.json()
    assert data_profile["total_e2e_latency_ms"] <= 700.0
    assert data_profile["is_within_budget"] is True

    # POST /api/v1/voice/simulate-turn
    sim_payload = {
        "user_transcript": "Can you summarize the top risks?",
        "simulate_interruption": False
    }
    resp_sim = client.post("/api/v1/voice/simulate-turn", json=sim_payload)
    assert resp_sim.status_code == 200
    data_sim = resp_sim.json()
    assert data_sim["interrupted"] is False
    assert len(data_sim["timeline_events"]) > 0

    # POST /api/v1/voice/barge-in/{session_id}
    resp_barge = client.post(f"/api/v1/voice/barge-in/{data_sim['session_id']}")
    assert resp_barge.status_code == 200
    assert resp_barge.json()["status"] == "barge_in_handled"


# ==========================================
# Salesforce Agentforce & Data Cloud Tests
# ==========================================

def test_salesforce_opportunity_listing_and_metadata():
    """
    Verify Salesforce CRM opportunities are seeded and retrieved.
    """
    opps = salesforce_service.list_opportunities()
    assert len(opps) >= 2
    
    apex_opp = next(o for o in opps if "Apex" in o.account_name)
    assert apex_opp.amount_usd == 10_000_000.0
    assert apex_opp.lead_partner == "Sarah Jenkins"


def test_agentforce_invocable_actions_metadata():
    """
    Verify Agentforce Invocable Actions metadata provides valid OpenAPI specifications.
    """
    actions = salesforce_service.get_agentforce_actions_metadata()
    action_names = [a["name"] for a in actions]
    
    assert "RunDiligenceAudit" in action_names
    assert "GetInvestmentScorecard" in action_names
    assert "PostChatterMemoSummary" in action_names


def test_agentforce_action_execution_flow():
    """
    Verify executing Agentforce Invocable Actions:
    1. RunDiligenceAudit
    2. GetInvestmentScorecard
    3. PostChatterMemoSummary
    """
    opp_id = "006Dn000003ABC1"

    # Action 1: RunDiligenceAudit
    audit_req = AgentforceActionRequest(
        action_name="RunDiligenceAudit",
        opportunity_id=opp_id
    )
    audit_res = salesforce_service.execute_agentforce_action(audit_req)
    assert audit_res.success is True
    assert audit_res.output_parameters["status"] == "COMPLETED"
    assert audit_res.output_parameters["composite_score"] == 88.0

    # Action 2: GetInvestmentScorecard
    scorecard_req = AgentforceActionRequest(
        action_name="GetInvestmentScorecard",
        opportunity_id=opp_id
    )
    scorecard_res = salesforce_service.execute_agentforce_action(scorecard_req)
    assert scorecard_res.success is True
    assert scorecard_res.output_parameters["arr_usd"] == 12_500_000.0
    assert scorecard_res.output_parameters["nrr_pct"] == 128.0

    # Action 3: PostChatterMemoSummary
    chatter_req = AgentforceActionRequest(
        action_name="PostChatterMemoSummary",
        opportunity_id=opp_id
    )
    chatter_res = salesforce_service.execute_agentforce_action(chatter_req)
    assert chatter_res.success is True
    assert chatter_res.chatter_post_created is True
    assert "0D5Dn0000" in chatter_res.output_parameters["chatter_post_id"]


def test_salesforce_data_cloud_zero_copy_sync():
    """
    Verify Data Cloud Zero-Copy federation queries live lakehouse DMOs.
    """
    sync_res = salesforce_service.sync_data_cloud_zero_copy()
    assert sync_res.sync_status == "FEDERATED_ACTIVE"
    assert sync_res.records_ingested >= 2
    assert "ssot__Opportunity__dlm" in sync_res.zero_copy_tables


def test_salesforce_rest_api_endpoints():
    """
    Test REST endpoints for Salesforce opportunities, Agentforce execution, and Data Cloud sync.
    """
    # 1. GET /api/v1/salesforce/opportunities
    resp_opps = client.get("/api/v1/salesforce/opportunities")
    assert resp_opps.status_code == 200
    assert len(resp_opps.json()) >= 2

    # 2. GET /api/v1/salesforce/agentforce/actions
    resp_actions = client.get("/api/v1/salesforce/agentforce/actions")
    assert resp_actions.status_code == 200
    assert len(resp_actions.json()) >= 3

    # 3. POST /api/v1/salesforce/agentforce/execute
    exec_payload = {
        "action_name": "GetInvestmentScorecard",
        "opportunity_id": "006Dn000003ABC1"
    }
    resp_exec = client.post("/api/v1/salesforce/agentforce/execute", json=exec_payload)
    assert resp_exec.status_code == 200
    assert resp_exec.json()["success"] is True

    # 4. POST /api/v1/salesforce/data-cloud/sync
    resp_sync = client.post("/api/v1/salesforce/data-cloud/sync")
    assert resp_sync.status_code == 200
    assert resp_sync.json()["sync_status"] == "FEDERATED_ACTIVE"
