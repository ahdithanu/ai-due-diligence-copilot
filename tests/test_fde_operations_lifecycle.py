import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.main import app
from backend.db.database import AsyncSessionLocal, init_db
from backend.db.models import InvestmentModel, GraphCheckpointModel
from backend.domain.schemas import (
    OnboardingStage,
    DeploymentReadinessReport,
    CanaryResult,
    FDEObservabilityMetrics,
    DeploymentConfig
)
from backend.services.deployment_service import (
    init_seed_deployments,
    create_deployment,
    get_deployment
)
from backend.services.acceptance_gate_service import run_acceptance_gate
from backend.services.canary_service import run_canary_test
from backend.services.customer_onboarding_service import (
    get_onboarding_status,
    advance_onboarding_stage,
    get_fde_observability_metrics
)


def test_onboarding_stage_enum():
    assert OnboardingStage.DISCOVER == "DISCOVER"
    assert OnboardingStage.CONFIGURE == "CONFIGURE"
    assert OnboardingStage.VALIDATE == "VALIDATE"
    assert OnboardingStage.EVALUATE == "EVALUATE"
    assert OnboardingStage.PILOT == "PILOT"
    assert OnboardingStage.OBSERVE == "OBSERVE"
    assert OnboardingStage.TUNE == "TUNE"
    assert OnboardingStage.ACCEPT == "ACCEPT"
    assert OnboardingStage.EXPAND == "EXPAND"


@pytest.mark.asyncio
async def test_acceptance_gate_service_and_api():
    async with AsyncSessionLocal() as session:
        await init_seed_deployments(session)

        # 1. Test direct service call for valid seed deployment
        report = await run_acceptance_gate("growth_saas_default", session)
        assert isinstance(report, DeploymentReadinessReport)
        assert report.deployment_id == "growth_saas_default"
        assert report.status == "READY"
        assert len(report.checks) >= 5
        assert all(check.passed for check in report.checks)

        # 2. Test direct service call for non-existent deployment
        bad_report = await run_acceptance_gate("non_existent_dep_xyz", session)
        assert bad_report.status == "NOT_READY"
        assert bad_report.checks[0].passed is False

    # 3. Test API endpoint GET /api/v1/operations/acceptance-gate/{deployment_id}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/operations/acceptance-gate/growth_saas_default")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deployment_id"] == "growth_saas_default"
        assert data["status"] == "READY"
        assert len(data["checks"]) >= 5

        bad_resp = await client.get("/api/v1/operations/acceptance-gate/invalid_dep_999")
        assert bad_resp.status_code == 200
        bad_data = bad_resp.json()
        assert bad_data["status"] == "NOT_READY"


@pytest.mark.asyncio
async def test_canary_engine_execution_and_teardown():
    async with AsyncSessionLocal() as session:
        # 1. Test direct service call
        result = await run_canary_test(session)
        assert isinstance(result, CanaryResult)
        assert result.passed is True
        assert result.synthetic_investment_id.startswith("canary-")
        assert result.node_checkpoints_verified > 0
        assert result.conflict_resolved is True
        assert result.teardown_successful is True
        assert result.duration_ms > 0.0

        # Verify DB teardown: synthetic investment record must not exist
        inv_check = await session.execute(
            select(InvestmentModel).where(InvestmentModel.id == result.synthetic_investment_id)
        )
        assert inv_check.scalar_one_or_none() is None

        ckpt_check = await session.execute(
            select(GraphCheckpointModel).where(GraphCheckpointModel.investment_id == result.synthetic_investment_id)
        )
        assert len(ckpt_check.scalars().all()) == 0

    # 2. Test API endpoint POST /api/v1/operations/canary-test
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/operations/canary-test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        assert data["synthetic_investment_id"].startswith("canary-")
        assert data["teardown_successful"] is True
        assert data["node_checkpoints_verified"] > 0


@pytest.mark.asyncio
async def test_customer_onboarding_lifecycle_progression():
    dep_id = f"onboarding_dep_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        # Create deployment profile
        config = DeploymentConfig(
            deployment_id=dep_id,
            customer_name="Acme Capital Partners",
            deployment_name="Acme Diligence Suite",
            investment_strategy="growth_equity_saas"
        )
        await create_deployment(session, config)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Initial Onboarding State should be DISCOVER
        get_resp = await client.get(f"/api/v1/operations/onboarding/{dep_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["current_stage"] == "DISCOVER"
        assert data["is_complete"] is False

        # 2. Advance stage step-by-step through all 9 stages: DISCOVER -> EXPAND
        expected_stages = [
            "CONFIGURE", "VALIDATE", "EVALUATE", "PILOT",
            "OBSERVE", "TUNE", "ACCEPT", "EXPAND"
        ]

        for stage in expected_stages:
            adv_resp = await client.post(f"/api/v1/operations/onboarding/{dep_id}/advance")
            assert adv_resp.status_code == 200
            adv_data = adv_resp.json()
            assert adv_data["current_stage"] == stage

        # 3. Final state at EXPAND should be complete
        final_get = await client.get(f"/api/v1/operations/onboarding/{dep_id}")
        assert final_get.status_code == 200
        final_data = final_get.json()
        assert final_data["current_stage"] == "EXPAND"
        assert final_data["is_complete"] is True
        assert len(final_data["stage_history"]) >= 9

        # 4. Test advancing with explicit target_stage parameter
        target_resp = await client.post(
            f"/api/v1/operations/onboarding/{dep_id}/advance",
            params={"target_stage": "CONFIGURE"}
        )
        assert target_resp.status_code == 200
        target_data = target_resp.json()
        assert target_data["current_stage"] == "CONFIGURE"
        assert target_data["is_complete"] is False


@pytest.mark.asyncio
async def test_fde_observability_metrics_aggregation():
    async with AsyncSessionLocal() as session:
        metrics = await get_fde_observability_metrics(session)
        assert isinstance(metrics, FDEObservabilityMetrics)
        assert 0.0 <= metrics.request_error_rate <= 1.0
        assert 0.0 <= metrics.graph_execution_failure_rate <= 1.0
        assert metrics.model_average_latency_ms > 0.0
        assert metrics.total_model_cost_usd >= 0.0
        assert metrics.queue_depth >= 0
        assert 0.0 <= metrics.checkpoint_failure_rate <= 1.0
        assert 0.0 <= metrics.human_escalation_rate <= 1.0
        assert 0.0 <= metrics.autonomous_completion_rate <= 1.0
        assert 0.0 <= metrics.recovery_success_rate <= 1.0

    # Test API GET /api/v1/operations/metrics
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/operations/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "request_error_rate" in data
        assert "graph_execution_failure_rate" in data
        assert "model_average_latency_ms" in data
        assert "total_model_cost_usd" in data
        assert "queue_depth" in data
        assert "checkpoint_failure_rate" in data
        assert "human_escalation_rate" in data
        assert "autonomous_completion_rate" in data
        assert "recovery_success_rate" in data
