from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.domain.schemas import DeploymentConfig
from backend.services.deployment_service import (
    create_deployment,
    get_deployment,
    list_deployments
)

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("", response_model=List[DeploymentConfig])
async def get_deployments(db: AsyncSession = Depends(get_db)):
    models = await list_deployments(db)
    results = []
    for model in models:
        if model.config_json:
            results.append(DeploymentConfig.model_validate(model.config_json))
        else:
            results.append(
                DeploymentConfig(
                    deployment_id=model.id,
                    customer_name=model.customer_name,
                    deployment_name=model.deployment_name,
                    investment_strategy=model.investment_strategy
                )
            )
    return results

@router.post("", response_model=DeploymentConfig, status_code=status.HTTP_201_CREATED)
async def create_new_deployment(
    config: DeploymentConfig,
    db: AsyncSession = Depends(get_db)
):
    existing = await get_deployment(db, config.deployment_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deployment with id '{config.deployment_id}' already exists."
        )
    created_model = await create_deployment(db, config)
    return DeploymentConfig.model_validate(created_model.config_json)

@router.get("/{deployment_id}", response_model=DeploymentConfig)
async def get_deployment_by_id(
    deployment_id: str,
    db: AsyncSession = Depends(get_db)
):
    model = await get_deployment(db, deployment_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{deployment_id}' not found."
        )
    if model.config_json:
        return DeploymentConfig.model_validate(model.config_json)
    return DeploymentConfig(
        deployment_id=model.id,
        customer_name=model.customer_name,
        deployment_name=model.deployment_name,
        investment_strategy=model.investment_strategy
    )
