from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.domain.schemas import (
    SalesforceOpportunity,
    AgentforceActionRequest,
    AgentforceActionResponse,
    SalesforceDataCloudSyncResult
)
from backend.services.salesforce_service import salesforce_service

router = APIRouter(prefix="/salesforce", tags=["Salesforce Agentforce & Data Cloud"])


@router.get("/opportunities", response_model=List[SalesforceOpportunity])
async def list_opportunities() -> List[SalesforceOpportunity]:
    """
    Returns pipeline opportunities synced from Salesforce CRM / Data Cloud.
    """
    return salesforce_service.list_opportunities()


@router.get("/agentforce/actions")
async def get_agentforce_actions() -> List[Dict[str, Any]]:
    """
    Returns OpenAPI-compliant Invocable Action definitions for Salesforce Agentforce
    and External Services catalog.
    """
    return salesforce_service.get_agentforce_actions_metadata()


@router.post("/agentforce/execute", response_model=AgentforceActionResponse)
async def execute_agentforce_action(
    request: AgentforceActionRequest
) -> AgentforceActionResponse:
    """
    Executes an action called by Salesforce Agentforce or Flow.
    Supports RunDiligenceAudit, GetInvestmentScorecard, and PostChatterMemoSummary.
    """
    return salesforce_service.execute_agentforce_action(request)


@router.post("/data-cloud/sync", response_model=SalesforceDataCloudSyncResult)
async def sync_data_cloud() -> SalesforceDataCloudSyncResult:
    """
    Executes a Salesforce Data Cloud Zero-Copy federation query.
    Directly accesses CRM Lakehouse objects without ETL pipelines.
    """
    return salesforce_service.sync_data_cloud_zero_copy()
