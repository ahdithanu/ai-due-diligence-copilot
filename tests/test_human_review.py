import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    MaterialityLevel,
    ContradictionRecord,
    ClaimNode,
    ClaimType,
    SpecialistAnalysis
)
from backend.nodes.human_review_node import HumanReviewGateNode


@pytest.mark.asyncio
async def test_human_review_gate_triggers_material_contradiction():
    state = DiligenceState(
        investment_id="inv-gate-1",
        company_name="ContradictCorp",
        industry="SaaS",
        target_round="Series A",
        contradictions=[
            ContradictionRecord(
                claim_a_id="c1",
                claim_b_id="c2",
                description="Pitch deck states $10M ARR while audit report states $6M ARR.",
                materiality=MaterialityLevel.CRITICAL,
                status="OPEN"
            )
        ]
    )

    gate_node = HumanReviewGateNode()
    updated_state = await gate_node.execute(state)

    assert updated_state.human_review_required is True
    assert updated_state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("Material contradiction detected" in r for r in updated_state.human_review_reasons)


@pytest.mark.asyncio
async def test_human_review_gate_triggers_low_confidence():
    state = DiligenceState(
        investment_id="inv-gate-2",
        company_name="LowConf Inc",
        industry="HealthTech",
        target_round="Seed",
        confidence_score=0.45
    )

    gate_node = HumanReviewGateNode()
    updated_state = await gate_node.execute(state)

    assert updated_state.human_review_required is True
    assert updated_state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("0.45" in r and "below threshold" in r for r in updated_state.human_review_reasons)


@pytest.mark.asyncio
async def test_human_review_gate_triggers_max_iterations():
    state = DiligenceState(
        investment_id="inv-gate-3",
        company_name="IterLoop Corp",
        industry="AI",
        target_round="Pre-Seed",
        iteration_counts={"FinancialAnalystGenerator": 3}
    )

    gate_node = HumanReviewGateNode(max_iterations=3)
    updated_state = await gate_node.execute(state)

    assert updated_state.human_review_required is True
    assert updated_state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("Max iteration limit (3) reached" in r for r in updated_state.human_review_reasons)


@pytest.mark.asyncio
async def test_human_review_gate_triggers_unverified_assumptions():
    state = DiligenceState(
        investment_id="inv-gate-4",
        company_name="AssumeTech",
        industry="CleanTech",
        target_round="Series B",
        assumptions=[
            ClaimNode(
                text="Customer retention will remain 95% post price increase",
                claim_type=ClaimType.ASSUMPTION,
                materiality=MaterialityLevel.HIGH
            )
        ]
    )

    gate_node = HumanReviewGateNode()
    updated_state = await gate_node.execute(state)

    assert updated_state.human_review_required is True
    assert updated_state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("Unverified assumptions present" in r for r in updated_state.human_review_reasons)


@pytest.mark.asyncio
async def test_resume_and_rerun_diligence_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create investment workspace
        create_resp = await client.post(
            "/api/v1/investments",
            json={
                "company_name": "Apex Quantum",
                "industry": "DeepTech",
                "target_round": "Series A",
                "check_size_usd": 3000000.0
            }
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investment_id"]

        # 2. Trigger initial graph execution
        start_resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/start?domain=Financial")
        assert start_resp.status_code == 200

        # 3. Resume with APPROVE action
        resume_resp = await client.post(
            f"/api/v1/investments/{inv_id}/diligence/resume",
            json={
                "action": "APPROVE",
                "human_feedback": "Approved after reviewing team credentials."
            }
        )
        assert resume_resp.status_code == 200
        resumed_state = resume_resp.json()
        assert resumed_state["human_review_required"] is False
        assert any(log["node_name"] == "HumanReviewGateNode" for log in resumed_state["execution_history"])

        # 4. Resume with ADD_EVIDENCE action
        evidence_resp = await client.post(
            f"/api/v1/investments/{inv_id}/diligence/resume",
            json={
                "action": "ADD_EVIDENCE",
                "human_feedback": "Supplied audited financials.",
                "new_evidence": [
                    {
                        "content": "Verified FY24 Revenue is $12.5M audited by EY.",
                        "claim_type": "FACT",
                        "confidence": 0.98
                    }
                ]
            }
        )
        assert evidence_resp.status_code == 200
        ev_state = evidence_resp.json()
        assert len(ev_state["evidence_records"]) >= 1
        assert any("Verified FY24 Revenue" in ev["content"] for ev in ev_state["evidence_records"])

        # 5. Rerun graph execution
        rerun_resp = await client.post(
            f"/api/v1/investments/{inv_id}/diligence/rerun",
            json={"domain": "Financial"}
        )
        assert rerun_resp.status_code == 200
        rerun_state = rerun_resp.json()
        assert rerun_state["investment_id"] == inv_id

        # 6. Resume with REJECT action
        reject_resp = await client.post(
            f"/api/v1/investments/{inv_id}/diligence/resume",
            json={
                "action": "REJECT",
                "human_feedback": "Deal declined due to unmitigated IP litigation risk."
            }
        )
        assert reject_resp.status_code == 200
        rejected_state = reject_resp.json()
        assert rejected_state["status"] == DiligenceStatus.FAILED.value
