import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    AgentEvaluationResult,
    SpecialistAnalysis
)
from backend.engine.model_adapter import MockModelAdapter
from backend.engine.node import BaseNode
from backend.engine.graph import GraphEngine, END
from backend.engine.analyst_critic_loop import (
    AnalystGeneratorNode,
    CriticEvaluatorNode,
    analyst_critic_judge_condition,
    build_analyst_critic_graph
)

class SampleNode(BaseNode):
    def __init__(self, name: str = "SampleNode"):
        super().__init__(name=name)

    async def process(self, state: DiligenceState) -> DiligenceState:
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


@pytest.mark.asyncio
async def test_node_execution():
    state = DiligenceState(
        investment_id="inv-123",
        company_name="Acme AI",
        industry="Enterprise Software",
        target_round="Series A"
    )
    node = SampleNode("TestNode")
    updated_state = await node.execute(state, iteration=1)

    assert updated_state.status == DiligenceStatus.SPECIALIST_DILIGENCE
    assert len(updated_state.execution_history) == 1
    log = updated_state.execution_history[0]
    assert log.node_name == "TestNode"
    assert log.status == "COMPLETED"
    assert log.iteration == 1
    assert log.end_time is not None


@pytest.mark.asyncio
async def test_analyst_critic_loop_pass():
    state = DiligenceState(
        investment_id="inv-456",
        company_name="BioHealth Inc",
        industry="Biotech",
        target_round="Seed"
    )
    model_adapter = MockModelAdapter()
    model_adapter.set_evaluation_behavior(overall_pass=True)

    graph = build_analyst_critic_graph(domain="Financial", model_adapter=model_adapter)
    final_state = await graph.run(state)

    assert "Financial" in final_state.specialist_analyses
    analysis = final_state.specialist_analyses["Financial"]
    assert analysis.passed_evaluation is True
    assert len(final_state.evaluations) == 1
    assert final_state.evaluations[0].overall_pass is True
    assert final_state.iteration_counts["FinancialAnalystGenerator"] == 1


@pytest.mark.asyncio
async def test_critic_loop_routing_and_revision():
    state = DiligenceState(
        investment_id="inv-789",
        company_name="Quantum Compute",
        industry="Hardware",
        target_round="Series B"
    )
    model_adapter = MockModelAdapter()

    eval_count = 0

    def dynamic_response(prompt: str):
        nonlocal eval_count
        eval_count += 1
        # Fail on first evaluation call, pass on second
        is_pass = eval_count >= 2
        return AgentEvaluationResult(
            evaluator_name="FinancialCriticEvaluator",
            target_node="FinancialAnalystGenerator",
            overall_pass=is_pass,
            evidence_coverage_score=0.9 if is_pass else 0.5,
            citation_correctness_score=0.9 if is_pass else 0.5,
            logical_consistency_score=0.9 if is_pass else 0.5,
            financial_correctness_score=0.9 if is_pass else 0.5,
            completeness_score=0.9 if is_pass else 0.5,
            critique_feedback=[] if is_pass else ["Missing ARR citation."]
        )

    model_adapter.register_response(AgentEvaluationResult, dynamic_response)

    graph = build_analyst_critic_graph(domain="Financial", model_adapter=model_adapter)
    final_state = await graph.run(state)

    # Analyst generator ran twice (iteration 1 failed critic, iteration 2 passed)
    assert final_state.iteration_counts["FinancialAnalystGenerator"] == 2
    assert len(final_state.evaluations) == 2
    assert final_state.evaluations[0].overall_pass is False
    assert final_state.evaluations[1].overall_pass is True
    assert final_state.specialist_analyses["Financial"].passed_evaluation is True


@pytest.mark.asyncio
async def test_score_evaluation_failure():
    state = DiligenceState(
        investment_id="inv-score",
        company_name="ScoreTech",
        industry="SaaS",
        target_round="Seed"
    )

    # Create analyst node & critic node with high threshold
    analyst_node = AnalystGeneratorNode(domain="Market")
    critic_node = CriticEvaluatorNode(
        target_analyst_node_name=analyst_node.name,
        domain="Market",
        score_threshold=0.8
    )

    model_adapter = MockModelAdapter()
    model_adapter.set_evaluation_behavior(
        overall_pass=True,
        scores={
            "evidence_coverage_score": 0.60,  # Below 0.8
            "citation_correctness_score": 0.85,
            "logical_consistency_score": 0.85,
            "financial_correctness_score": 0.85,
            "completeness_score": 0.85,
        }
    )
    critic_node.model_adapter = model_adapter

    state = await analyst_node.execute(state)
    state = await critic_node.execute(state)

    eval_res = state.evaluations[-1]
    assert eval_res.overall_pass is False
    assert len(eval_res.critique_feedback) > 0


@pytest.mark.asyncio
async def test_max_iteration_fallback():
    state = DiligenceState(
        investment_id="inv-max-iter",
        company_name="FailCorp",
        industry="AI",
        target_round="Pre-Seed"
    )

    model_adapter = MockModelAdapter()
    model_adapter.set_evaluation_behavior(
        overall_pass=False,
        scores={
            "evidence_coverage_score": 0.40,
            "citation_correctness_score": 0.40,
            "logical_consistency_score": 0.40,
            "financial_correctness_score": 0.40,
            "completeness_score": 0.40,
        }
    )

    graph = build_analyst_critic_graph(domain="Risk", model_adapter=model_adapter, max_iterations=3)
    final_state = await graph.run(state)

    assert final_state.iteration_counts["RiskAnalystGenerator"] == 3
    assert final_state.human_review_required is True
    assert final_state.status == DiligenceStatus.HUMAN_REVIEW
    assert any("Max iteration limit (3) reached" in reason for reason in final_state.human_review_reasons)


@pytest.mark.asyncio
async def test_diligence_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create investment workspace
        create_payload = {
            "company_name": "Solaris Robotics",
            "industry": "CleanTech",
            "target_round": "Series A",
            "check_size_usd": 5000000.0
        }
        create_resp = await client.post("/api/v1/investments", json=create_payload)
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investment_id"]

        # 2. Trigger graph execution via POST /api/v1/investments/{id}/diligence/start
        start_resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/start?domain=Financial")
        assert start_resp.status_code == 200
        state_data = start_resp.json()
        assert state_data["investment_id"] == inv_id
        assert "Financial" in state_data["specialist_analyses"]

        # 3. Fetch execution logs via GET /api/v1/investments/{id}/diligence/logs
        logs_resp = await client.get(f"/api/v1/investments/{inv_id}/diligence/logs")
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        assert len(logs) >= 2
        node_names = [log["node_name"] for log in logs]
        assert "FinancialCritic" in node_names

        assert logs[0]["status"] == "COMPLETED"
