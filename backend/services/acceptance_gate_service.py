from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.deployment_service import get_deployment
from backend.domain.schemas import (
    DeploymentConfig,
    PreflightCheckResult,
    DeploymentReadinessReport
)

async def run_acceptance_gate(deployment_id: str, db: AsyncSession) -> DeploymentReadinessReport:
    """
    Evaluates pre-flight deployment readiness for a given deployment profile.
    Performs checks on configuration completeness, financial thresholds, model roles, tool integrations, and escalation rules.
    """
    checks: List[PreflightCheckResult] = []

    dep_model = await get_deployment(db, deployment_id)
    if not dep_model:
        checks.append(PreflightCheckResult(
            check_name="Deployment Profile Existence",
            passed=False,
            details=f"Deployment profile configuration for '{deployment_id}' was not found in database."
        ))
        return DeploymentReadinessReport(
            deployment_id=deployment_id,
            status="NOT_READY",
            checks=checks,
            evaluated_at=datetime.now(timezone.utc)
        )

    config = None
    if dep_model.config_json:
        try:
            config = DeploymentConfig.model_validate(dep_model.config_json)
        except Exception as e:
            checks.append(PreflightCheckResult(
                check_name="Deployment Schema Validation",
                passed=False,
                details=f"Failed to parse deployment configuration JSON: {str(e)}"
            ))
            return DeploymentReadinessReport(
                deployment_id=deployment_id,
                status="NOT_READY",
                checks=checks,
                evaluated_at=datetime.now(timezone.utc)
            )

    checks.append(PreflightCheckResult(
        check_name="Deployment Profile Existence",
        passed=True,
        details=f"Deployment profile '{deployment_id}' ({dep_model.customer_name}) loaded successfully."
    ))

    # 1. Required Diligence Sections Check
    sections = config.required_diligence_sections if config else []
    if sections:
        checks.append(PreflightCheckResult(
            check_name="Required Diligence Sections",
            passed=True,
            details=f"Configured with {len(sections)} sections: {', '.join(sections[:3])}{'...' if len(sections) > 3 else ''}"
        ))
    else:
        checks.append(PreflightCheckResult(
            check_name="Required Diligence Sections",
            passed=False,
            details="No required diligence sections configured."
        ))

    # 2. Financial & Risk Thresholds Check
    fin_th = config.financial_thresholds if config else {}
    risk_th = config.risk_thresholds if config else {}
    if fin_th and risk_th:
        checks.append(PreflightCheckResult(
            check_name="Financial & Risk Thresholds",
            passed=True,
            details=f"{len(fin_th)} financial thresholds and {len(risk_th)} risk thresholds configured."
        ))
    elif fin_th or risk_th:
        checks.append(PreflightCheckResult(
            check_name="Financial & Risk Thresholds",
            passed=False,
            details="Partial thresholds configured (missing financial or risk threshold definitions)."
        ))
    else:
        checks.append(PreflightCheckResult(
            check_name="Financial & Risk Thresholds",
            passed=False,
            details="No financial or risk thresholds configured."
        ))

    # 3. Model Pipeline & Routing Policy Check
    models = config.enabled_models if config else []
    roles = config.model_roles if config else {}
    if models and ("synthesizer" in roles or "extractor" in roles):
        checks.append(PreflightCheckResult(
            check_name="Model Routing & Pipeline Setup",
            passed=True,
            details=f"Enabled models: {', '.join(models)}. Roles assigned: {list(roles.keys())}"
        ))
    else:
        checks.append(PreflightCheckResult(
            check_name="Model Routing & Pipeline Setup",
            passed=False,
            details="Enabled models or required model roles ('synthesizer', 'extractor') missing."
        ))

    # 4. Allowed Tools Integration Check
    tools = config.allowed_tools if config else []
    if tools:
        checks.append(PreflightCheckResult(
            check_name="Tool Integrations Setup",
            passed=True,
            details=f"{len(tools)} tools enabled: {', '.join(tools)}"
        ))
    else:
        checks.append(PreflightCheckResult(
            check_name="Tool Integrations Setup",
            passed=False,
            details="No allowed tools enabled in deployment config."
        ))

    # 5. Human Escalation Rules Check
    rules = config.human_escalation_rules if config else []
    if rules:
        checks.append(PreflightCheckResult(
            check_name="Human Escalation Rules",
            passed=True,
            details=f"{len(rules)} escalation rules defined."
        ))
    else:
        checks.append(PreflightCheckResult(
            check_name="Human Escalation Rules",
            passed=False,
            details="No human escalation rules configured."
        ))

    # Determine readiness status
    failed_checks = [c for c in checks if not c.passed]
    if not failed_checks:
        status = "READY"
    elif len(failed_checks) <= 2 and checks[0].passed and checks[3].passed:
        status = "READY_WITH_RISKS"
    else:
        status = "NOT_READY"

    return DeploymentReadinessReport(
        deployment_id=deployment_id,
        status=status,
        checks=checks,
        evaluated_at=datetime.now(timezone.utc)
    )
