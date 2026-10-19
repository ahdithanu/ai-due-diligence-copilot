from fastapi import APIRouter, HTTPException, Response
from typing import Optional

from backend.domain.schemas import (
    DiligenceChecklistResponse,
    ChecklistTask,
    CreateTaskRequest,
    UpdateTaskRequest,
    ValuationCompsResponse,
)
from backend.services.diligence_checklist_service import diligence_checklist_service
from backend.services.valuation_comps_service import valuation_comps_service
from backend.services.financial_model_excel_service import financial_model_excel_service

router = APIRouter(tags=["Diligence Hub & Institutional Tools"])


@router.get(
    "/investments/{investment_id}/checklist",
    response_model=DiligenceChecklistResponse,
    summary="Get multi-workstream private equity diligence checklist",
)
async def get_diligence_checklist(investment_id: str):
    return diligence_checklist_service.get_checklist(investment_id)


@router.post(
    "/investments/{investment_id}/checklist/tasks",
    response_model=ChecklistTask,
    summary="Add a new diligence task to a workstream",
)
async def create_checklist_task(investment_id: str, request: CreateTaskRequest):
    return diligence_checklist_service.create_task(investment_id, request)


@router.patch(
    "/investments/{investment_id}/checklist/tasks/{task_id}",
    response_model=ChecklistTask,
    summary="Update status or findings of a diligence task",
)
async def update_checklist_task(
    investment_id: str, task_id: str, request: UpdateTaskRequest
):
    task = diligence_checklist_service.update_task(investment_id, task_id, request)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete(
    "/investments/{investment_id}/checklist/tasks/{task_id}",
    summary="Delete a diligence task",
)
async def delete_checklist_task(investment_id: str, task_id: str):
    success = diligence_checklist_service.delete_task(investment_id, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": task_id}


@router.get(
    "/investments/{investment_id}/valuation-comps",
    response_model=ValuationCompsResponse,
    summary="Get public SaaS multiples, precedent M&A comps, and Football Field valuation ranges",
)
async def get_valuation_comps(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
    arr: Optional[float] = 10_000_000.0,
    valuation: Optional[float] = 50_000_000.0,
):
    return valuation_comps_service.calculate_valuation_comps(
        investment_id=investment_id,
        company_name=company_name,
        arr_usd=arr,
        current_valuation_usd=valuation,
    )


@router.get(
    "/investments/{investment_id}/financial-model/download-xlsx",
    summary="Download complete 5-tab institutional financial model and cap table in Microsoft Excel (.xlsx)",
)
async def download_financial_model_excel(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
    arr: Optional[float] = 10_000_000.0,
    valuation: Optional[float] = 50_000_000.0,
):
    excel_bytes = financial_model_excel_service.generate_excel_model(
        company_name=company_name,
        arr_usd=arr,
        valuation_usd=valuation,
    )
    filename = f"{company_name.lower().replace(' ', '_')}_financial_model.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


from backend.domain.schemas import (
    RemediationPlanResponse,
    ConditionPrecedent,
    UpdateConditionRequest,
    ValueCreationMilestone,
    CreateMilestoneRequest,
    ExternalIntelligenceResponse,
)
from backend.services.remediation_covenants_service import remediation_covenants_service
from backend.services.external_intel_service import external_intelligence_service


@router.get(
    "/investments/{investment_id}/remediation-plan",
    response_model=RemediationPlanResponse,
    summary="Get pre-closing conditions precedent, escrows, covenants, and 100-day value creation roadmap",
)
async def get_remediation_plan(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
    valuation: Optional[float] = 50_000_000.0,
):
    return remediation_covenants_service.get_remediation_plan(
        investment_id=investment_id,
        company_name=company_name,
        valuation_usd=valuation,
    )


@router.patch(
    "/investments/{investment_id}/remediation-plan/conditions/{cp_id}",
    response_model=ConditionPrecedent,
    summary="Update condition precedent status (SATISFIED / PENDING / WAIVED)",
)
async def update_condition_precedent(
    investment_id: str, cp_id: str, req: UpdateConditionRequest
):
    cp = remediation_covenants_service.update_condition_status(
        investment_id, cp_id, req.status
    )
    if not cp:
        raise HTTPException(status_code=404, detail="Condition Precedent not found")
    return cp


@router.post(
    "/investments/{investment_id}/remediation-plan/milestones",
    response_model=ValueCreationMilestone,
    summary="Add a milestone to the 100-day value creation roadmap",
)
async def add_value_creation_milestone(
    investment_id: str, req: CreateMilestoneRequest
):
    return remediation_covenants_service.add_milestone(investment_id, req)


@router.get(
    "/investments/{investment_id}/external-intel",
    response_model=ExternalIntelligenceResponse,
    summary="Get external market intelligence, competitor funding, executive roster, and organizational health metrics",
)
async def get_external_intelligence(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
):
    return external_intelligence_service.get_external_intel(
        investment_id=investment_id,
        company_name=company_name,
    )

