import pytest
import json
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.domain.schemas import DiligenceState, DiligenceStatus
from backend.engine.model_adapter import MockModelAdapter
from backend.engine.node import BaseNode
from backend.engine.graph import GraphEngine, END
from backend.engine.analyst_critic_loop import build_analyst_critic_graph

class SampleTestNode(BaseNode):
    def __init__(self, name: str = "SampleTestNode"):
        super().__init__(name=name)

    async def process(self, state: DiligenceState) -> DiligenceState:
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state

@pytest.mark.asyncio
async def test_run_stream_yields_events_in_sequence():
    state = DiligenceState(
        investment_id="inv-sse-123",
        company_name="StreamTech AI",
        industry="SaaS",
        target_round="Series A"
    )

    graph = GraphEngine("test_stream_graph")
    node = SampleTestNode("SampleTestNode")
    graph.add_node("SampleTestNode", node)
    graph.set_entry_point("SampleTestNode")
    graph.add_edge("SampleTestNode", END)

    events = []
    async for event_line in graph.run_stream(state):
        assert event_line.startswith("data: ")
        json_str = event_line.replace("data: ", "").strip()
        if json_str:
            events.append(json.loads(json_str))

    assert len(events) >= 3
    # 1. First event should be node_start
    assert events[0]["event"] == "node_start"
    assert events[0]["node"] == "SampleTestNode"
    assert events[0]["iteration"] == 1

    # 2. Second event should be node_complete
    assert events[1]["event"] == "node_complete"
    assert events[1]["node"] == "SampleTestNode"
    assert isinstance(events[1]["duration_ms"], (int, float))
    assert "evaluation" in events[1]

    # 3. Final event should be diligence_complete
    assert events[-1]["event"] == "diligence_complete"
    assert events[-1]["status"] == DiligenceStatus.SPECIALIST_DILIGENCE.value


@pytest.mark.asyncio
async def test_run_stream_human_review_event():
    state = DiligenceState(
        investment_id="inv-sse-hr",
        company_name="ReviewCorp",
        industry="Hardware",
        target_round="Seed"
    )

    model_adapter = MockModelAdapter()
    model_adapter.set_evaluation_behavior(
        overall_pass=False,
        scores={
            "evidence_coverage_score": 0.3,
            "citation_correctness_score": 0.3,
            "logical_consistency_score": 0.3,
            "financial_correctness_score": 0.3,
            "completeness_score": 0.3,
        }
    )

    graph = build_analyst_critic_graph(domain="Financial", model_adapter=model_adapter, max_iterations=1)

    events = []
    async for event_line in graph.run_stream(state):
        if event_line.startswith("data: "):
            json_str = event_line.replace("data: ", "").strip()
            if json_str:
                events.append(json.loads(json_str))

    event_types = [e["event"] for e in events]
    assert "node_start" in event_types
    assert "node_complete" in event_types
    assert "human_review" in event_types

    hr_event = next(e for e in events if e["event"] == "human_review")
    assert isinstance(hr_event["reasons"], list)
    assert len(hr_event["reasons"]) > 0


@pytest.mark.asyncio
async def test_diligence_stream_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create investment workspace
        create_resp = await client.post("/api/v1/investments", json={
            "company_name": "Stream Dynamics",
            "industry": "Cloud Computing",
            "target_round": "Series B",
            "check_size_usd": 10000000.0
        })
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investment_id"]

        # 2. Call GET /api/v1/investments/{id}/diligence/stream
        stream_resp = await client.get(f"/api/v1/investments/{inv_id}/diligence/stream")
        assert stream_resp.status_code == 200
        assert stream_resp.headers["content-type"].startswith("text/event-stream")

        lines = stream_resp.text.strip().split("\n")
        events = []
        for line in lines:
            if line.startswith("data: "):
                json_str = line.replace("data: ", "").strip()
                if json_str:
                    events.append(json.loads(json_str))

        assert len(events) > 0
        event_types = [e["event"] for e in events]
        assert "node_start" in event_types
        assert "node_complete" in event_types
        assert "diligence_complete" in event_types
