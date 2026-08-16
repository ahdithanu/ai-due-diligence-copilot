import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import InvestmentModel
from backend.domain.schemas import (
    DiligenceState, CapTableEntry, WaterfallScenario, WaterfallPayout,
    SensitivityMatrix, ChatMessage, DataRoomRequest, ICAudioScript,
    WaterfallRequest, SensitivityRequest, ChatRequest
)
from backend.services.waterfall_calculator import calculate_exit_waterfall
from backend.services.sensitivity_engine import run_sensitivity_stress_test
from backend.services.diligence_chat_service import process_diligence_chat
from backend.services.audio_ic_service import generate_ic_audio_script
from backend.services.teaser_generator import generate_investment_teaser

router = APIRouter(prefix="/investments", tags=["Institutional Services"])

async def get_investment_state_or_404(investment_id: str, db: AsyncSession) -> tuple[InvestmentModel, DiligenceState]:
    stmt = select(InvestmentModel).where(InvestmentModel.id == investment_id)
    result = await db.execute(stmt)
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")
    
    if inv.state_snapshot_json:
        try:
            state = DiligenceState.model_validate(inv.state_snapshot_json)
        except Exception:
            state = DiligenceState(
                investment_id=inv.id,
                company_name=inv.company_name,
                industry=inv.industry,
                target_round=inv.target_round,
                check_size_usd=inv.check_size_usd
            )
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd
        )
    return inv, state


@router.post("/{investment_id}/waterfall", response_model=WaterfallScenario)
async def calculate_waterfall_endpoint(
    investment_id: str,
    req: Optional[WaterfallRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)
    
    cap_table = (req.cap_table if req and req.cap_table else None)
    exit_val = (req.exit_valuation_usd if req and req.exit_valuation_usd is not None else 50_000_000.0)
    total_inv = (req.total_investment_usd if req and req.total_investment_usd is not None else (state.check_size_usd or 10_000_000.0))

    if not cap_table:
        cap_table = [
            CapTableEntry(
                share_class=f"{state.target_round or 'Series A'} Preferred",
                investor_name="Lead VC Fund",
                shares_held=3_000_000.0,
                ownership_pct=30.0,
                liquidation_preference_multiplier=1.0,
                is_participating=False,
                cap_multiplier=None
            ),
            CapTableEntry(
                share_class="Common",
                investor_name="Founders & Key Team",
                shares_held=7_000_000.0,
                ownership_pct=70.0,
                liquidation_preference_multiplier=0.0,
                is_participating=False,
                cap_multiplier=None
            )
        ]

    scenario = calculate_exit_waterfall(
        cap_table=cap_table,
        exit_valuation_usd=exit_val,
        total_investment_usd=total_inv
    )
    return scenario


@router.post("/{investment_id}/sensitivity", response_model=SensitivityMatrix)
async def calculate_sensitivity_endpoint(
    investment_id: str,
    req: Optional[SensitivityRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)

    metrics_input = req.financial_metrics if (req and req.financial_metrics) else {}
    if not metrics_input and state.financial_metrics:
        for fm in state.financial_metrics:
            metrics_input[fm.metric_name.lower()] = fm.value

    if "runway_months" not in metrics_input and "runway" not in metrics_input:
        metrics_input["runway_months"] = 18.0
    if "ebitda_margin_pct" not in metrics_input and "ebitda_margin" not in metrics_input:
        metrics_input["ebitda_margin_pct"] = -15.0
    if "cac_payback_months" not in metrics_input and "cac_payback" not in metrics_input:
        metrics_input["cac_payback_months"] = 12.0

    return run_sensitivity_stress_test(metrics_input)


@router.post("/{investment_id}/chat")
async def chat_diligence_endpoint(
    investment_id: str,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)

    user_msg = ChatMessage(role="user", content=req.question)
    state.chat_history.append(user_msg)

    assistant_msg, new_requests = process_diligence_chat(state, req.question)
    state.chat_history.append(assistant_msg)
    
    for r in new_requests:
        if not any(existing.document_needed.lower() == r.document_needed.lower() for existing in state.data_room_requests):
            state.data_room_requests.append(r)

    inv.state_snapshot_json = state.model_dump(mode="json")
    await db.commit()

    return {
        "message": assistant_msg,
        "data_room_requests_generated": new_requests,
        "evidence_citations": assistant_msg.evidence_citations
    }


@router.get("/{investment_id}/data-room-requests", response_model=List[DataRoomRequest])
async def get_data_room_requests_endpoint(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)

    if not state.data_room_requests:
        default_requests = [
            DataRoomRequest(
                category="Financial",
                document_needed="2-Year Audited Financial Statements & Monthly P&L Model",
                priority="HIGH",
                status="PENDING",
                rationale="Audit revenue recognition and historical gross margins."
            ),
            DataRoomRequest(
                category="Commercial",
                document_needed="Customer Cohort Net Retention & Logo Churn Schedule",
                priority="HIGH",
                status="PENDING",
                rationale="Evaluate enterprise logo retention and expansion kinetics."
            ),
            DataRoomRequest(
                category="Legal & Corporate",
                document_needed="Fully Diluted Cap Table & IP Proprietary Rights Assignment",
                priority="HIGH",
                status="PENDING",
                rationale="Verify equity ownership and core software asset IP protection."
            )
        ]
        state.data_room_requests.extend(default_requests)
        inv.state_snapshot_json = state.model_dump(mode="json")
        await db.commit()

    return state.data_room_requests


@router.get("/{investment_id}/ic-audio-script", response_model=ICAudioScript)
async def get_ic_audio_script_endpoint(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)

    script = generate_ic_audio_script(state)
    state.ic_audio_script = script
    inv.state_snapshot_json = state.model_dump(mode="json")
    await db.commit()

    return script


@router.get("/{investment_id}/teaser")
async def get_investment_teaser_endpoint(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    inv, state = await get_investment_state_or_404(investment_id, db)

    teaser_result = generate_investment_teaser(state)
    state.teaser_markdown = teaser_result["teaser_markdown"]
    inv.state_snapshot_json = state.model_dump(mode="json")
    await db.commit()

    return teaser_result
