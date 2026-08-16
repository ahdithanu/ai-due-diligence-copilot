from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.domain.schemas import (
    DeploymentReadinessReport,
    CanaryResult,
    FDEObservabilityMetrics,
    OnboardingStage
)
from backend.services.acceptance_gate_service import run_acceptance_gate
from backend.services.canary_service import run_canary_test
from backend.services.customer_onboarding_service import (
    get_onboarding_status,
    advance_onboarding_stage,
    get_fde_observability_metrics
)

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("/acceptance-gate/{deployment_id}", response_model=DeploymentReadinessReport)
async def get_acceptance_gate_report(
    deployment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates pre-flight deployment readiness for the specified deployment profile.
    """
    report = await run_acceptance_gate(deployment_id, db)
    return report


@router.post("/canary-test", response_model=CanaryResult)
async def trigger_canary_test(
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers an automated end-to-end canary test verifying graph health and database teardown.
    """
    result = await run_canary_test(db)
    return result


@router.get("/onboarding/{deployment_id}")
async def get_customer_onboarding_state(
    deployment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the customer onboarding stage and progress metrics for a deployment.
    """
    status_info = await get_onboarding_status(deployment_id, db)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment profile '{deployment_id}' not found."
        )
    return status_info


@router.post("/onboarding/{deployment_id}/advance")
async def advance_customer_onboarding_stage(
    deployment_id: str,
    target_stage: Optional[OnboardingStage] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Advances the onboarding stage for a deployment to the next stage or specified target_stage.
    """
    updated_info = await advance_onboarding_stage(deployment_id, target_stage, db)
    if not updated_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment profile '{deployment_id}' not found."
        )
    return updated_info


@router.get("/metrics", response_model=FDEObservabilityMetrics)
async def get_operations_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Calculates and returns system-wide FDE observability metrics.
    """
    metrics = await get_fde_observability_metrics(db)
    return metrics
