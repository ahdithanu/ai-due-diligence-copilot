import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.domain.schemas import StaffEditRequest, VerifyArtifactRequest
from backend.services.dreaming_service import dreaming_service
from backend.services.staff_feedback_eval_service import staff_feedback_eval_service
from backend.services.artifact_verifier_service import artifact_verifier_service
from backend.services.fee_and_conflict_scanner import fee_and_conflict_scanner
from backend.services.operational_knowledge_service import operational_knowledge_service
from eval.run_arca_evals import arca_eval_runner

client = TestClient(app)


def test_dreaming_service_and_api():
    inv_id = "test-dream-001"
    run_resp = dreaming_service.run_dreaming(inv_id, "Acme SaaS AI")
    assert run_resp.investment_id == inv_id
    assert run_resp.signals_consolidated_count >= 3
    assert run_resp.agent_readiness_score >= 90.0
    assert len(run_resp.key_invariants_updated) >= 3

    # API test
    post_resp = client.post(f"/api/v1/investments/{inv_id}/dreaming/run?company_name=TestCo")
    assert post_resp.status_code == 200
    assert post_resp.json()["agent_readiness_score"] >= 90.0

    get_resp = client.get(f"/api/v1/investments/{inv_id}/dreaming/latest")
    assert get_resp.status_code == 200
    assert "synthesized_deal_state_summary" in get_resp.json()


def test_staff_feedback_eval_service_and_api():
    inv_id = "test-staff-001"
    req = StaffEditRequest(
        target_field="proposed_entry_multiple",
        agent_original_value=14.5,
        human_adjusted_value=12.0,
        reason_why="Target gross margins contracted 4% in Q3; normalized peer multiples dictate 12.0x ceiling.",
        editor_role="Senior Partner",
    )
    rec = staff_feedback_eval_service.record_staff_edit(inv_id, req)
    assert rec.target_field == "proposed_entry_multiple"
    assert rec.eval_candidate_id.startswith("eval-cand-")

    # API test
    post_resp = client.post(
        f"/api/v1/investments/{inv_id}/staff-feedback",
        json={
            "target_field": "runway_months",
            "agent_original_value": 18.0,
            "human_adjusted_value": 14.5,
            "reason_why": "Discovered uncapitalized server equipment lease obligations.",
            "editor_role": "Deal Lead",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["eval_candidate_id"] is not None

    get_resp = client.get(f"/api/v1/investments/{inv_id}/staff-feedback")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) >= 1


def test_artifact_verifier_service_and_api():
    # Test 1: PII & Wire violation
    bad_content = "Wire the fund deposit to routing number 021000021 account 998877665544 immediately."
    rep = artifact_verifier_service.verify_artifact("funding_memo.pdf", bad_content)
    assert rep.passed is False
    assert rep.pii_violations_count > 0
    assert "[REDACTED_BANK_ACCOUNT]" in rep.sanitized_content

    # Test 2: Promissory return violation
    bad_memo = "We guarantee a minimum 4.0x MOIC with zero risk of capital loss."
    rep2 = artifact_verifier_service.verify_artifact("ic_memo.pdf", bad_memo)
    assert rep2.passed is False
    assert rep2.promissory_claims_count > 0

    # Test 3: Compliant memo
    good_memo = "The company reported $9.35M in ARR [rag-chunk-101] with an 80% gross margin [rag-chunk-102]. The model indicates an estimated 3.2x MOIC under base case conditions."
    rep3 = artifact_verifier_service.verify_artifact("clean_memo.pdf", good_memo)
    assert rep3.passed is True

    # API test
    resp = client.post(
        "/api/v1/investments/verify-artifact",
        json={"artifact_name": "memo.pdf", "content": bad_content},
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is False


def test_hidden_fee_scanner_and_api():
    inv_id = "test-fee-001"
    scan = fee_and_conflict_scanner.scan_investment_documents(inv_id)
    assert scan.total_annual_drag_usd >= 300_000.0
    assert len(scan.findings) >= 4
    categories = [f.category for f in scan.findings]
    assert "RELATED_PARTY" in categories
    assert "NON_FIDUCIARY" in categories
    assert "LIQUIDATION_RATCHET" in categories

    # API test
    resp = client.get(f"/api/v1/investments/{inv_id}/hidden-fees")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_annual_drag_usd"] >= 300_000.0


def test_operational_knowledge_service_and_api():
    items = operational_knowledge_service.list_knowledge_items()
    assert len(items) >= 4

    # Update knowledge
    item_id = items[0].id
    up = operational_knowledge_service.update_knowledge_item(
        item_id, "Updated Valuation Benchmark Standard", "# Updated Content", "Head of PE"
    )
    assert up is not None
    assert up.title == "Updated Valuation Benchmark Standard"
    assert up.citations_count >= 1

    # API test
    list_resp = client.get("/api/v1/operational-knowledge")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 4

    put_resp = client.put(
        f"/api/v1/operational-knowledge/{item_id}?title=API%20Title&content_markdown=%23%20Content&editor=Analyst"
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["title"] == "API Title"


def test_arca_golden_eval_suite_and_api():
    scorecard = arca_eval_runner.run_all_evals()
    assert scorecard.overall_firm_eval_pass_rate_pct == 100.0
    assert scorecard.edge_artifact_compliance_score_pct == 100.0
    assert scorecard.hidden_fee_detection_score_pct == 100.0
    assert scorecard.staff_feedback_capture_score_pct == 100.0
    assert scorecard.dreaming_synthesis_score_pct == 100.0

    # API test
    resp = client.get("/api/v1/evals/arca/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_firm_eval_pass_rate_pct"] == 100.0
    assert len(data["case_details"]) >= 9
