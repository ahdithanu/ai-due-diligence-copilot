import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.domain.schemas import DemoStep
from backend.services.automated_demo_service import automated_demo_service, STEP_METADATA


@pytest.fixture(autouse=True)
def reset_demo_service():
    automated_demo_service.reset()
    yield
    automated_demo_service.reset()


def test_automated_demo_service_progression():
    """
    Tests AutomatedDemoService step progression through all 8 milestones in sequence.
    """
    # Start service
    status = automated_demo_service.start(speed=1.5, loop=True)
    assert status.active is True
    assert status.paused is False
    assert status.current_step == DemoStep.DEPLOYMENT_SELECTION.value
    assert status.current_step_name == STEP_METADATA[0]["name"]
    assert status.active_tab == "deployments"
    assert status.progress_pct == 12.5
    assert status.loop_count == 0

    expected_steps = [
        (DemoStep.DOCUMENT_FINANCIAL_ENGINE, "financials", 25.0),
        (DemoStep.SPECIALIST_CRITIC_LOOP, "graph", 37.5),
        (DemoStep.CONTRADICTION_INTERRUPT, "evidence", 50.0),
        (DemoStep.CHECKPOINT_RECOVERY, "graph", 62.5),
        (DemoStep.IC_DEBATE_AND_MEMO, "ic_debate", 75.0),
        (DemoStep.FAILURE_LAB_FAILOVER, "failure_lab", 87.5),
        (DemoStep.ACCEPTANCE_AND_CANARY, "fde_ops", 100.0),
    ]

    for expected_step, expected_tab, expected_pct in expected_steps:
        status = automated_demo_service.step()
        assert status.current_step == expected_step.value
        assert status.active_tab == expected_tab
        assert status.progress_pct == expected_pct

    # Total 8 steps checked
    assert status.current_step == DemoStep.ACCEPTANCE_AND_CANARY.value
    assert status.progress_pct == 100.0


def test_automated_demo_service_loop_reset_behavior():
    """
    Tests loop reset behavior when loop=True.
    """
    status = automated_demo_service.start(speed=1.0, loop=True)

    # Step through to step 8 (ACCEPTANCE_AND_CANARY)
    for _ in range(7):
        status = automated_demo_service.step()
    assert status.current_step == DemoStep.ACCEPTANCE_AND_CANARY.value
    assert status.loop_count == 0

    # Stepping from step 8 when loop=True should reset to step 1 and increment loop_count
    status = automated_demo_service.step()
    assert status.current_step == DemoStep.DEPLOYMENT_SELECTION.value
    assert status.active_tab == "deployments"
    assert status.progress_pct == 12.5
    assert status.loop_count == 1
    assert any("Loop 1 completed" in log for log in status.log_messages)


def test_automated_demo_service_pause_resume():
    """
    Tests pause and resume functionality in AutomatedDemoService.
    """
    automated_demo_service.start()
    status = automated_demo_service.pause()
    assert status.paused is True

    status = automated_demo_service.resume()
    assert status.active is True
    assert status.paused is False


@pytest.mark.asyncio
async def test_demo_api_endpoints():
    """
    Tests Demo REST API endpoints (/start, /pause, /resume, /step, /reset, /status).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET /api/v1/demo/status (initial)
        resp = await client.get("/api/v1/demo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_step"] == DemoStep.DEPLOYMENT_SELECTION.value

        # POST /api/v1/demo/start
        start_payload = {"speed": 2.0, "loop": True}
        resp = await client.post("/api/v1/demo/start", json=start_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["active"] is True
        assert data["speed"] == 2.0
        assert data["auto_loop"] is True
        assert data["current_step"] == DemoStep.DEPLOYMENT_SELECTION.value

        # POST /api/v1/demo/pause
        resp = await client.post("/api/v1/demo/pause")
        assert resp.status_code == 200
        data = resp.json()
        assert data["paused"] is True

        # POST /api/v1/demo/resume
        resp = await client.post("/api/v1/demo/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active"] is True
        assert data["paused"] is False

        # POST /api/v1/demo/step (advance to step 2)
        resp = await client.post("/api/v1/demo/step")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_step"] == DemoStep.DOCUMENT_FINANCIAL_ENGINE.value
        assert data["progress_pct"] == 25.0

        # GET /api/v1/demo/status
        resp = await client.get("/api/v1/demo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_step"] == DemoStep.DOCUMENT_FINANCIAL_ENGINE.value

        # POST /api/v1/demo/reset
        resp = await client.post("/api/v1/demo/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active"] is False
        assert data["paused"] is False
        assert data["current_step"] == DemoStep.DEPLOYMENT_SELECTION.value
        assert data["loop_count"] == 0
