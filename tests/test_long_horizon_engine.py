import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.domain.schemas import (
    SignalType,
    SignalSource,
    IngestSignalRequest,
    ResolveActionRequest,
    CreateConstraintRequest,
    CreateMandateRequest,
)
from backend.services.long_horizon_service import long_horizon_service

client = TestClient(app)


def test_long_horizon_service_initialization():
    inv_id = "test-arca-deal-001"
    space = long_horizon_service.get_space(inv_id, "Acme SaaS AI")

    assert space.investment_id == inv_id
    assert space.active_agents_count >= 4
    assert space.signals_processed_count >= 3
    assert space.pending_actions_count >= 3
    assert len(space.durable_constraints) >= 3
    assert len(space.active_mandates) >= 2


def test_ingest_signal_and_agent_reaction():
    inv_id = "test-arca-deal-002"
    # External signal arrives from data room
    sig_req = IngestSignalRequest(
        signal_type=SignalType.DATA_ROOM_FILE_DROPPED,
        source=SignalSource.EXTERNAL_WORLD,
        title="Cap Table Drop: 'Series_A_Clean_Model.xlsx'",
        payload={"filename": "Series_A_Clean_Model.xlsx", "size_kb": 1200},
    )
    signal = long_horizon_service.ingest_signal(inv_id, sig_req)

    assert signal.signal_type == SignalType.DATA_ROOM_FILE_DROPPED
    assert "Cap Table & Dilution Sentry Agent" in signal.acting_agents

    # Verify a new partner action was proactively prepared by the agent
    space = long_horizon_service.get_space(inv_id)
    newest_action = space.pending_actions[0]
    assert "Series_A_Clean_Model.xlsx" in newest_action.headline or "Autonomous Analysis" in newest_action.headline
    assert newest_action.status == "PENDING_APPROVAL"


def test_resolve_partner_action_with_feedback_loop():
    inv_id = "test-arca-deal-003"
    space = long_horizon_service.get_space(inv_id)
    action_to_resolve = space.pending_actions[0]

    # Partner resolves action with 1-click approval
    res_req = ResolveActionRequest(
        approved=True,
        resolution_notes="Approved counter-proposal of $46.75M entry valuation.",
    )
    resolved = long_horizon_service.resolve_action(inv_id, action_to_resolve.id, res_req)

    assert resolved is not None
    assert resolved.status == "APPROVED"
    assert "Approved" in resolved.resolution_notes

    # Verify feedback loop: internal signal was emitted that will wake downstream agents
    updated_space = long_horizon_service.get_space(inv_id)
    top_signal = updated_space.recent_signals[0]
    assert top_signal.signal_type == SignalType.TASK_COMPLETED_BY_HUMAN
    assert top_signal.source == SignalSource.INTERNAL_UI


def test_durable_entity_constraints_and_firm_mandates():
    inv_id = "test-arca-deal-004"
    # Add durable target constraint
    c_req = CreateConstraintRequest(
        category="BOARD_CONTROL",
        rule_text="Founders explicitly rejected 3-seat investor majority on Day 12.",
        source="Partner Call Notes with Founder",
    )
    constraint = long_horizon_service.add_constraint(inv_id, c_req)
    assert constraint.category == "BOARD_CONTROL"
    assert constraint.is_active is True

    # Add firm-wide strategic mandate
    m_req = CreateMandateRequest(
        mandate_name="Zero-Trust LLM API Vendor Security Audit",
        description="Every portfolio company using 3rd-party LLMs must undergo zero-data-retention DLP verification.",
        target_frequency="ON_EVALUATION",
        enforcement_level="MANDATORY_ALL_DEALS",
    )
    mandate = long_horizon_service.add_mandate(m_req)
    assert mandate.mandate_name == "Zero-Trust LLM API Vendor Security Audit"
    assert mandate.active is True


def test_long_horizon_api_endpoints():
    inv_id = "test-arca-api-001"

    # GET Space
    resp = client.get(f"/api/v1/investments/{inv_id}/long-horizon/space")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_agents_count" in data
    assert "pending_actions" in data
    assert "recent_signals" in data
    assert "durable_constraints" in data
    assert "active_mandates" in data

    # POST Ingest Signal
    post_sig = client.post(
        f"/api/v1/investments/{inv_id}/long-horizon/signals",
        json={
            "signal_type": "FOUNDER_EMAIL_RECEIVED",
            "source": "EXTERNAL_WORLD",
            "title": "Email: Founder agrees to 1-year cliff on reverse vesting",
            "payload": {"sender": "elena@acme.ai"},
        },
    )
    assert post_sig.status_code == 200
    sig_data = post_sig.json()
    assert sig_data["signal_type"] == "FOUNDER_EMAIL_RECEIVED"

    # POST Resolve Action
    action_id = data["pending_actions"][0]["id"]
    post_res = client.post(
        f"/api/v1/investments/{inv_id}/long-horizon/actions/{action_id}/resolve",
        json={"approved": True, "resolution_notes": "1-Click Partner Approval"},
    )
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "APPROVED"

    # POST Create Constraint
    post_c = client.post(
        f"/api/v1/investments/{inv_id}/long-horizon/constraints",
        json={
            "category": "TAX_QSBS",
            "rule_text": "Target must remain C-Corp to maintain QSBS 100% tax shield.",
        },
    )
    assert post_c.status_code == 200
    assert post_c.json()["category"] == "TAX_QSBS"

    # POST & GET Mandates
    post_m = client.post(
        "/api/v1/investments/long-horizon/mandates",
        json={
            "mandate_name": "Automatic SOC2 Compliance Gate",
            "description": "Must fail gating if unmitigated SOC2 Type II audit gaps exist.",
            "target_frequency": "ON_EVALUATION",
            "enforcement_level": "MANDATORY_ALL_DEALS",
        },
    )
    assert post_m.status_code == 200

    get_m = client.get("/api/v1/investments/long-horizon/mandates")
    assert get_m.status_code == 200
    assert len(get_m.json()) >= 3
