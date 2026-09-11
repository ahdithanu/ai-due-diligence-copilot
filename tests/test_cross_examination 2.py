import pytest
from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    EvidenceRecord,
    ClaimType,
    MaterialityLevel,
    ClaimNode,
    SpecialistAnalysis,
    ContradictionRecord
)
from backend.nodes.specialist_nodes import RiskAnalystNode
from backend.nodes.cross_examiner_node import CrossExaminerNode
from backend.nodes.gap_detector_node import GapDetectorNode


@pytest.fixture
def contradiction_diligence_state() -> DiligenceState:
    state = DiligenceState(
        investment_id="inv_test_cross_exam",
        company_name="Veritas Cloud",
        industry="SaaS",
        target_round="Series B",
        check_size_usd=10000000.0
    )

    ev_deck = EvidenceRecord(
        id="ev_deck_rev",
        document_id="doc_pitch_deck",
        chunk_id="c_deck_1",
        content="Veritas Cloud achieved revenue of $18.5M ARR in FY2024 with 500 enterprise customers.",
        claim_type=ClaimType.FACT,
        page_number=2
    )

    ev_audit = EvidenceRecord(
        id="ev_audit_rev",
        document_id="doc_audited_financials",
        chunk_id="c_audit_1",
        content="Audited financial statement revenue for FY2024 is $12.0M with 220 active enterprise customers.",
        claim_type=ClaimType.FACT,
        page_number=15
    )

    state.evidence_records.extend([ev_deck, ev_audit])

    # Populate specialist analyses with claims
    financial_analysis = SpecialistAnalysis(
        domain="Financial",
        summary="Financial analysis of Veritas Cloud.",
        claims=[
            ClaimNode(
                id="claim_fin_deck",
                text="Pitch deck reports FY2024 revenue of $18.5M ARR.",
                claim_type=ClaimType.FACT,
                evidence_ids=[ev_deck.id],
                materiality=MaterialityLevel.HIGH
            ),
            ClaimNode(
                id="claim_fin_audit",
                text="Audited financial statements state FY2024 revenue of $12.0M.",
                claim_type=ClaimType.FACT,
                evidence_ids=[ev_audit.id],
                materiality=MaterialityLevel.CRITICAL
            )
        ]
    )

    customer_analysis = SpecialistAnalysis(
        domain="Customer",
        summary="Customer analysis of Veritas Cloud.",
        claims=[
            ClaimNode(
                id="claim_cust_deck",
                text="Pitch deck claims 500 enterprise customer accounts.",
                claim_type=ClaimType.FACT,
                evidence_ids=[ev_deck.id],
                materiality=MaterialityLevel.MEDIUM
            ),
            ClaimNode(
                id="claim_cust_audit",
                text="Audited metrics list 220 active customer accounts.",
                claim_type=ClaimType.FACT,
                evidence_ids=[ev_audit.id],
                materiality=MaterialityLevel.HIGH
            )
        ]
    )

    state.specialist_analyses["Financial"] = financial_analysis
    state.specialist_analyses["Customer"] = customer_analysis

    # Add a high materiality risk claim to risk_register
    risk_claim = ClaimNode(
        id="claim_risk_keyperson",
        text="Single point of failure on founder CEO and unhedged IP exposure.",
        claim_type=ClaimType.INFERENCE,
        evidence_ids=[ev_deck.id],
        materiality=MaterialityLevel.HIGH
    )
    state.risk_register.append(risk_claim)

    return state


@pytest.mark.asyncio
async def test_cross_examiner_node_detection(contradiction_diligence_state):
    node = CrossExaminerNode()
    updated_state = await node.execute(contradiction_diligence_state)

    assert updated_state.status == DiligenceStatus.CROSS_EXAMINATION
    assert len(updated_state.contradictions) > 0

    # Verify contradiction record attributes
    contra: ContradictionRecord = updated_state.contradictions[0]
    assert contra.claim_a_id is not None
    assert contra.claim_b_id is not None
    assert contra.description != ""
    assert contra.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]
    assert contra.status == "OPEN"

    # Human review should be triggered due to high materiality contradictions
    assert updated_state.human_review_required is True
    assert len(updated_state.human_review_reasons) > 0


@pytest.mark.asyncio
async def test_gap_detector_node_question_ranking(contradiction_diligence_state):
    # Run cross examiner first so contradictions exist in state
    cross_node = CrossExaminerNode()
    state = await cross_node.execute(contradiction_diligence_state)

    # Run gap detector
    gap_node = GapDetectorNode()
    final_state = await gap_node.execute(state)

    assert len(final_state.open_questions) > 0

    # Verify open questions properties
    q0 = final_state.open_questions[0]
    assert q0.question != ""
    assert q0.reason_it_matters != ""
    assert q0.related_risk_or_thesis != ""
    assert q0.required_evidence != ""
    assert q0.status == "OPEN"

    # Check question priority ranking (priority 1 should come before priority 2/3)
    priorities = [q.priority for q in final_state.open_questions]
    assert priorities == sorted(priorities), f"Open questions should be sorted by priority ascending, got {priorities}"

    # Priority 1 questions should correspond to critical contradictions
    assert any(q.priority == 1 and "discrepancy" in q.question.lower() for q in final_state.open_questions)
