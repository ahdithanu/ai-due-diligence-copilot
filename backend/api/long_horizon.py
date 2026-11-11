from fastapi import APIRouter, HTTPException
from typing import Optional, List

from backend.domain.schemas import (
    LongHorizonSpaceResponse,
    SignalEvent,
    IngestSignalRequest,
    PartnerActionItem,
    ResolveActionRequest,
    DurableConstraint,
    CreateConstraintRequest,
    FirmStrategicMandate,
    CreateMandateRequest,
)
from backend.services.long_horizon_service import long_horizon_service

router = APIRouter(tags=["Arca Long-Horizon Autonomous Engine"])


@router.get(
    "/investments/{investment_id}/long-horizon/space",
    response_model=LongHorizonSpaceResponse,
    summary="Get Arca-style autonomous collaborative deal space, watchers, action inbox, and entity memory",
)
async def get_long_horizon_space(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
):
    return long_horizon_service.get_space(investment_id, company_name)


@router.post(
    "/investments/{investment_id}/long-horizon/signals",
    response_model=SignalEvent,
    summary="Ingest an external or internal world signal (founder email, data room drop, custodian event) and trigger interested agents",
)
async def ingest_world_signal(
    investment_id: str,
    req: IngestSignalRequest,
):
    return long_horizon_service.ingest_signal(investment_id, req)


@router.post(
    "/investments/{investment_id}/long-horizon/actions/{action_id}/resolve",
    response_model=PartnerActionItem,
    summary="Resolve an executive action item ('Agents Prompt Humans') with a 1-click approval or rejection",
)
async def resolve_partner_action(
    investment_id: str,
    action_id: str,
    req: ResolveActionRequest,
):
    action = long_horizon_service.resolve_action(investment_id, action_id, req)
    if not action:
        raise HTTPException(status_code=404, detail="Action item not found")
    return action


@router.post(
    "/investments/{investment_id}/long-horizon/constraints",
    response_model=DurableConstraint,
    summary="Record durable target entity memory and prohibited terms across 30-day deal horizon",
)
async def add_durable_constraint(
    investment_id: str,
    req: CreateConstraintRequest,
):
    return long_horizon_service.add_constraint(investment_id, req)


@router.post(
    "/investments/long-horizon/mandates",
    response_model=FirmStrategicMandate,
    summary="Set top-down firm-wide strategic goal or mandate to steer agents across all deals",
)
async def create_firm_mandate(
    req: CreateMandateRequest,
):
    return long_horizon_service.add_mandate(req)


@router.get(
    "/investments/long-horizon/mandates",
    response_model=List[FirmStrategicMandate],
    summary="List active firm-wide strategic mandates",
)
async def list_firm_mandates():
    return long_horizon_service._mandates
