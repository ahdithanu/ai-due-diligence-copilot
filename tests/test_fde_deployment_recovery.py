import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.main import app
from backend.db.database import AsyncSessionLocal
from backend.db.models import InvestmentModel, GraphCheckpointModel, ExecutionFailureModel
from backend.domain.schemas import (
    DiligenceState, DiligenceStatus, ExecutionState,
    EvidenceRecord, FinancialMetricRecord, ContradictionRecord, MaterialityLevel,
    ClaimNode, ClaimType
)
from backend.services.deployment_service import (
    get_default_growth_saas_config,
    get_default_traditional_buyout_config,
    init_seed_deployments
)
from backend.nodes.financial_analyst_node import FinancialAnalystNode, DeterministicFinancialEngineNode
from backend.nodes.specialist_nodes import UnitEconomicsAnalystNode, RiskAnalystNode
from backend.engine.graph import GraphEngine, END
from backend.engine.node import BaseNode
from backend.engine.pipeline_builder import build_full_diligence_graph
from backend.engine.model_adapter import MockModelAdapter


@pytest.mark.asyncio
async def test_multi_deployment_behavior_saas_vs_buyout():
    """
    Tests that Growth Equity SaaS vs Traditional Buyout deployment configs
    cause nodes to emphasize different financial & risk metrics.
    """
    saas_config = get_default_growth_saas_config()
    buyout_config = get_default_traditional_buyout_config()

    saas_state = DiligenceState(
        investment_id=f"inv_saas_{uuid.uuid4().hex[:6]}",
        company_name="SaaSify Inc",
        industry="Enterprise Software",
        target_round="Series B",
        deployment_id=saas_config.deployment_id,
        deployment_config=saas_config,
        financial_metrics=[
            FinancialMetricRecord(metric_name="ARR_Growth", value=45.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Net_Revenue_Retention", value=115.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="CAC_Payback", value=14.0, unit="months", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Rule_of_40", value=42.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="EBITDA_Margin", value=-10.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Leverage_Ratio", value=1.5, unit="ratio", period="FY2024", formula="Formula")
        ]
    )

    buyout_state = DiligenceState(
        investment_id=f"inv_buyout_{uuid.uuid4().hex[:6]}",
        company_name="Legacy Manufacturing Co",
        industry="Industrial Manufacturing",
        target_round="Buyout",
        deployment_id=buyout_config.deployment_id,
        deployment_config=buyout_config,
        financial_metrics=[
            FinancialMetricRecord(metric_name="EBITDA_Margin", value=22.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Leverage_Ratio", value=3.2, unit="ratio", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Cash_Conversion", value=0.85, unit="ratio", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="Working_Capital", value=5000000.0, unit="USD", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="ARR_Growth", value=5.0, unit="%", period="FY2024", formula="Formula"),
            FinancialMetricRecord(metric_name="CAC_Payback", value=28.0, unit="months", period="FY2024", formula="Formula")
        ]
    )

    financial_node = FinancialAnalystNode()
    unit_node = UnitEconomicsAnalystNode()
    risk_node = RiskAnalystNode()

    # Process SaaS state
    saas_state = await financial_node.process(saas_state)
    saas_state = await unit_node.process(saas_state)
    saas_state = await risk_node.process(saas_state)

    fin_saas = saas_state.specialist_analyses["Financial"]
    assert "Growth Equity SaaS" in fin_saas.summary
    assert "ARR growth, NRR, CAC payback, Rule of 40" in fin_saas.summary
    assert any("Strong" in s for s in fin_saas.strengths)

    # Process Buyout state
    buyout_state = await financial_node.process(buyout_state)
    buyout_state = await unit_node.process(buyout_state)
    buyout_state = await risk_node.process(buyout_state)

    fin_buyout = buyout_state.specialist_analyses["Financial"]
    assert "Traditional Buyout" in fin_buyout.summary
    assert "EBITDA margin, leverage, cash conversion, working capital" in fin_buyout.summary
    assert any("EBITDA margin" in s for s in fin_buyout.strengths)


@pytest.mark.asyncio
async def test_checkpoint_persistence_and_point_in_time_restoration():
    """
    Tests node checkpoint persistence in DB and point-in-time state restoration via start_from_checkpoint.
    """
    inv_id = f"inv_cp_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        inv = InvestmentModel(
            id=inv_id,
            company_name="Checkpoint Tech Inc",
            industry="Software",
            target_round="Series A",
            status=DiligenceStatus.CREATED.value
        )
        session.add(inv)
        await session.commit()

        initial_state = DiligenceState(
            investment_id=inv_id,
            company_name="Checkpoint Tech Inc",
            industry="Software",
            target_round="Series A"
        )

        model_adapter = MockModelAdapter()
        graph = build_full_diligence_graph(model_adapter=model_adapter)

        final_state = await graph.run(initial_state, db_session=session)
        assert len(final_state.checkpoint_history) > 0

        # Query DB for persisted GraphCheckpointModel records
        stmt = select(GraphCheckpointModel).where(GraphCheckpointModel.investment_id == inv_id).order_by(GraphCheckpointModel.timestamp.asc())
        result = await session.execute(stmt)
        checkpoints = result.scalars().all()
        assert len(checkpoints) >= 2

        # Select a middle checkpoint and restore state from it
        target_cp = checkpoints[1]
        restored_state = await graph.start_from_checkpoint(target_cp.id, db_session=session)
        assert restored_state.investment_id == inv_id
        assert restored_state.execution_state == ExecutionState.COMPLETED


@pytest.mark.asyncio
async def test_deliberate_failure_and_operator_retry():
    """
    Tests deliberate node failure state transition (ExecutionState.FAILED + FailureDetails)
    and operator retry recovery via API /api/v1/investments/{id}/diligence/retry.
    """
    class FailingNode(BaseNode):
        def __init__(self):
            super().__init__(name="FailingTestNode", description="Node designed to fail")

        async def process(self, state: DiligenceState) -> DiligenceState:
            raise RuntimeError("Deliberate execution failure for testing")

    inv_id = f"inv_fail_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        inv = InvestmentModel(
            id=inv_id,
            company_name="Faulty Cloud Inc",
            industry="Cloud",
            target_round="Seed",
            status=DiligenceStatus.CREATED.value
        )
        session.add(inv)
        await session.commit()

        initial_state = DiligenceState(
            investment_id=inv_id,
            company_name="Faulty Cloud Inc",
            industry="Cloud",
            target_round="Seed"
        )

        test_graph = GraphEngine(name="test_failure_graph")
        test_graph.add_node("FailingTestNode", FailingNode())
        test_graph.set_entry_point("FailingTestNode")

        failed_state = await test_graph.run(initial_state, db_session=session)
        assert failed_state.execution_state == ExecutionState.FAILED
        assert failed_state.status == DiligenceStatus.FAILED
        assert failed_state.failure_details is not None
        assert failed_state.failure_details.failed_node == "FailingTestNode"
        assert failed_state.failure_details.error_type == "RuntimeError"
        assert "Deliberate execution failure" in failed_state.failure_details.error_message
        assert failed_state.failure_details.retryable is True

        # Check DB failure record
        stmt = select(ExecutionFailureModel).where(ExecutionFailureModel.investment_id == inv_id)
        result = await session.execute(stmt)
        db_fail = result.scalar_one_or_none()
        assert db_fail is not None
        assert db_fail.failed_node == "FailingTestNode"

    # Operator Retry via API Endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        retry_resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/retry", json={"failed_node": "EntryNode"})
        assert retry_resp.status_code == 200
        retried_state = retry_resp.json()
        assert retried_state["execution_state"] in ["RUNNING", "COMPLETED", "WAITING_FOR_HUMAN"]
        assert retried_state["failure_details"] is None


@pytest.mark.asyncio
async def test_deterministic_evidence_conflict_resolution_and_recovery():
    """
    Tests evidence conflict ($12M Pitch Deck vs $8M Audited Financials ARR conflict),
    WAITING_FOR_HUMAN pause, operator conflict resolution, and checkpoint recovery.
    """
    inv_id = f"inv_conflict_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        inv = InvestmentModel(
            id=inv_id,
            company_name="Conflict SaaS Inc",
            industry="Enterprise Software",
            target_round="Series B",
            status=DiligenceStatus.CREATED.value
        )
        session.add(inv)

        ev1_id = f"ev_pitch_{uuid.uuid4().hex[:6]}"
        ev2_id = f"ev_audited_{uuid.uuid4().hex[:6]}"

        config = get_default_growth_saas_config()
        state = DiligenceState(
            investment_id=inv_id,
            company_name="Conflict SaaS Inc",
            industry="Enterprise Software",
            target_round="Series B",
            deployment_id=config.deployment_id,
            deployment_config=config,
            evidence_records=[
                EvidenceRecord(
                    id=ev1_id,
                    document_id="doc_pitch_deck",
                    chunk_id="chunk_1",
                    content="Company ARR reached $12.0M at the end of Q4 2024 according to pitch deck presentation.",
                    section_title="Executive Summary",
                    confidence=0.8
                ),
                EvidenceRecord(
                    id=ev2_id,
                    document_id="doc_audited_financials",
                    chunk_id="chunk_2",
                    content="Verified audited annual recurring revenue (ARR) for FY2024 is $8.0M with low regulatory risk exposure.",
                    section_title="Audited Financial Statements",
                    confidence=1.0
                )
            ],
            financial_metrics=[
                FinancialMetricRecord(
                    metric_name="ARR",
                    value=12.0,
                    unit="USD_Millions",
                    period="FY2024",
                    formula="Pitch Deck Claim",
                    input_evidence_ids=[ev1_id]
                )
            ],
            contradictions=[
                ContradictionRecord(
                    claim_a_id=ev1_id,
                    claim_b_id=ev2_id,
                    description="Material revenue contradiction: Pitch deck claims $12M ARR while audited financials state $8M ARR.",
                    materiality=MaterialityLevel.CRITICAL,
                    status="OPEN"
                )
            ],
            human_review_required=True,
            human_review_reasons=["Material contradiction detected: $12M vs $8M ARR"],
            execution_state=ExecutionState.WAITING_FOR_HUMAN,
            status=DiligenceStatus.HUMAN_REVIEW
        )

        inv.state_snapshot_json = state.model_dump(mode="json")
        await session.commit()

    # Call operator conflict resolution endpoint with authoritative evidence set to $8M ARR
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resolve_payload = {
            "authoritative_evidence_id": ev2_id,
            "resolved_value": 8.0,
            "resolution_notes": "Audited financials chosen as authoritative source. ARR resolved to $8M."
        }
        resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/resolve_conflict", json=resolve_payload)
        assert resp.status_code == 200
        resolved_state = resp.json()
        print("REASONS:", resolved_state["human_review_reasons"])
        print("EXEC STATE:", resolved_state["execution_state"])

        assert resolved_state["human_review_required"] is False
        assert resolved_state["execution_state"] in ["RUNNING", "COMPLETED"]
        # Check contradictions resolved
        for c in resolved_state["contradictions"]:
            assert c["status"] == "RESOLVED"
        # Check metrics updated to $8.0M
        for fm in resolved_state["financial_metrics"]:
            if fm["metric_name"] == "ARR":
                assert fm["value"] == 8.0
