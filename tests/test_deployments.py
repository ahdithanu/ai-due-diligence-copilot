import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.main import app
from backend.db.database import AsyncSessionLocal
from backend.db.models import DeploymentModel, GraphCheckpointModel, ExecutionFailureModel
from backend.domain.schemas import (
    ExecutionState, RedFlagSeverity, DeploymentConfig, FailureDetails,
    CheckpointRecord, DiligenceState, DiligenceStatus
)
from backend.services.deployment_service import (
    get_default_growth_saas_config,
    get_default_traditional_buyout_config,
    create_deployment,
    get_deployment,
    list_deployments,
    init_seed_deployments
)

def test_execution_state_enum():
    assert ExecutionState.RUNNING == "RUNNING"
    assert ExecutionState.PAUSED == "PAUSED"
    assert ExecutionState.FAILED == "FAILED"
    assert ExecutionState.WAITING_FOR_HUMAN == "WAITING_FOR_HUMAN"
    assert ExecutionState.COMPLETED == "COMPLETED"
    assert ExecutionState.CANCELLED == "CANCELLED"

def test_red_flag_severity_enum():
    assert RedFlagSeverity.CRITICAL == "CRITICAL"
    assert RedFlagSeverity.HIGH == "HIGH"
    assert RedFlagSeverity.MEDIUM == "MEDIUM"

def test_deployment_config_model():
    config = DeploymentConfig(
        deployment_id="test_dep_01",
        customer_name="Test Capital",
        deployment_name="Test SaaS Profile",
        investment_strategy="growth_equity_saas",
        required_diligence_sections=["financial_metrics", "unit_economics"],
        financial_thresholds={"min_gross_margin": 0.70},
        risk_thresholds={"max_customer_concentration_pct": "20%"},
        required_evidence_types=["audited_financials"],
        evaluation_thresholds={"min_quality_score": 0.85},
        human_escalation_rules=["gross_margin_below_threshold"],
        enabled_models=["gemini-2.5-pro"],
        model_roles={"synthesizer": "gemini-2.5-pro"},
        allowed_tools=["financial_calculator"],
        output_requirements={"format": "ic_memo"},
        custom_terminology={"ARR": "Annual Recurring Revenue"}
    )
    assert config.customer_name == "Test Capital"
    assert config.investment_strategy == "growth_equity_saas"

    dumped = config.model_dump(mode="json")
    validated = DeploymentConfig.model_validate(dumped)
    assert validated.deployment_id == "test_dep_01"
    assert validated.financial_thresholds["min_gross_margin"] == 0.70

def test_failure_details_and_checkpoint_record():
    failure = FailureDetails(
        failed_node="financial_specialist",
        error_type="ValidationError",
        error_message="Gross margin formula calculation failed",
        retryable=True,
        suggested_recovery_action="Retry node execution with fallback model"
    )
    assert failure.failed_node == "financial_specialist"
    assert failure.retryable is True

    checkpoint = CheckpointRecord(
        execution_id="exec_100",
        deployment_id="dep_100",
        investment_id="inv_100",
        node_id="evidence_extractor",
        graph_state_version=1,
        iteration_count=0,
        routing_decision="proceed_to_specialists",
        status=ExecutionState.RUNNING
    )
    assert checkpoint.execution_id == "exec_100"
    assert checkpoint.status == ExecutionState.RUNNING

def test_diligence_state_with_deployment_fields():
    config = get_default_growth_saas_config()
    state = DiligenceState(
        investment_id="inv_500",
        company_name="CloudScale Inc",
        industry="Enterprise Software",
        target_round="Series B",
        deployment_id=config.deployment_id,
        deployment_config=config,
        execution_state=ExecutionState.RUNNING
    )
    assert state.deployment_id == "growth_saas_default"
    assert state.deployment_config.customer_name == "Apex SaaS Capital"
    assert state.execution_state == ExecutionState.RUNNING
    assert len(state.checkpoint_history) == 0

def test_default_service_configs():
    saas = get_default_growth_saas_config()
    assert saas.investment_strategy == "growth_equity_saas"
    assert saas.financial_thresholds["min_gross_margin"] == 0.75

    buyout = get_default_traditional_buyout_config()
    assert buyout.investment_strategy == "traditional_buyout"
    assert buyout.financial_thresholds["min_ebitda_margin_pct"] == 0.15

@pytest.mark.asyncio
async def test_deployment_db_service():
    async with AsyncSessionLocal() as session:
        # Test init_seed_deployments
        await init_seed_deployments(session)

        deps = await list_deployments(session)
        dep_ids = [d.id for d in deps]
        assert "growth_saas_default" in dep_ids
        assert "traditional_buyout_default" in dep_ids

        # Test get_deployment
        fetched = await get_deployment(session, "growth_saas_default")
        assert fetched is not None
        assert fetched.customer_name == "Apex SaaS Capital"

        # Test creating custom deployment
        dep_id = f"custom_dep_{uuid.uuid4().hex[:8]}"
        custom_config = DeploymentConfig(
            deployment_id=dep_id,
            customer_name="Vanguard Venture Partners",
            deployment_name="Early Stage AI Fund Profile",
            investment_strategy="growth_equity_saas",
            financial_thresholds={"min_gross_margin": 0.80}
        )
        created = await create_deployment(session, custom_config)
        assert created.id == dep_id

        fetched_custom = await get_deployment(session, dep_id)
        assert fetched_custom is not None
        assert fetched_custom.customer_name == "Vanguard Venture Partners"

@pytest.mark.asyncio
async def test_deployments_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET /api/v1/deployments
        list_resp = await client.get("/api/v1/deployments")
        assert list_resp.status_code == 200
        deployments = list_resp.json()
        assert len(deployments) >= 2
        strategies = [d["investment_strategy"] for d in deployments]
        assert "growth_equity_saas" in strategies

        # POST /api/v1/deployments
        dep_id = f"api_test_dep_{uuid.uuid4().hex[:8]}"
        new_dep_payload = {
            "deployment_id": dep_id,
            "customer_name": "Frontier Horizon Ventures",
            "deployment_name": "BioTech Growth Strategy",
            "investment_strategy": "growth_equity_saas",
            "required_diligence_sections": ["clinical_trials", "financial_metrics"],
            "financial_thresholds": {"min_gross_margin": 0.65},
            "risk_thresholds": {"min_runway_months": "24"},
            "required_evidence_types": ["fda_approval_letter"],
            "evaluation_thresholds": {"min_quality_score": 0.90, "max_iterations": 2.0},
            "human_escalation_rules": ["fda_rejection_risk"],
            "enabled_models": ["gemini-2.5-pro"],
            "model_roles": {"synthesizer": "gemini-2.5-pro"},
            "allowed_tools": ["document_parser"],
            "output_requirements": {"format": "biotech_memo"},
            "custom_terminology": {"IND": "Investigational New Drug"}
        }
        post_resp = await client.post("/api/v1/deployments", json=new_dep_payload)
        assert post_resp.status_code == 201
        post_data = post_resp.json()
        assert post_data["deployment_id"] == dep_id
        assert post_data["customer_name"] == "Frontier Horizon Ventures"

        # GET /api/v1/deployments/{dep_id}
        get_resp = await client.get(f"/api/v1/deployments/{dep_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["deployment_name"] == "BioTech Growth Strategy"

