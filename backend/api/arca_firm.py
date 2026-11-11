from fastapi import APIRouter, HTTPException
from typing import Optional, List

from backend.domain.schemas import (
    DreamingRunResponse,
    StaffEditFeedbackRecord,
    StaffEditRequest,
    ArtifactComplianceReport,
    VerifyArtifactRequest,
    HiddenFeeScanResponse,
    OperationalKnowledgeItem,
    ArcaEvalScorecard,
)
from backend.services.dreaming_service import dreaming_service
from backend.services.staff_feedback_eval_service import staff_feedback_eval_service
from backend.services.artifact_verifier_service import artifact_verifier_service
from backend.services.fee_and_conflict_scanner import fee_and_conflict_scanner
from backend.services.operational_knowledge_service import operational_knowledge_service
from eval.run_arca_evals import arca_eval_runner

router = APIRouter(tags=["Arca AI-Native Firm Capabilities & Evals"])


@router.post(
    "/investments/{investment_id}/dreaming/run",
    response_model=DreamingRunResponse,
    summary="Trigger the autonomous dreaming reflection process to consolidate 30-day deal memory and invariants",
)
async def run_deal_dreaming(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
):
    return dreaming_service.run_dreaming(investment_id, company_name)


@router.get(
    "/investments/{investment_id}/dreaming/latest",
    response_model=DreamingRunResponse,
    summary="Retrieve the latest consolidated deal state of the world from the dreaming engine",
)
async def get_latest_deal_dreaming(
    investment_id: str,
    company_name: Optional[str] = "Acme SaaS AI",
):
    return dreaming_service.get_latest_dreaming(investment_id, company_name)


@router.post(
    "/investments/{investment_id}/staff-feedback",
    response_model=StaffEditFeedbackRecord,
    summary="Record a human staff adjustment with mandatory 'Why' reason and pipe into eval candidate store",
)
async def record_staff_feedback(
    investment_id: str,
    req: StaffEditRequest,
):
    return staff_feedback_eval_service.record_staff_edit(investment_id, req)


@router.get(
    "/investments/{investment_id}/staff-feedback",
    response_model=List[StaffEditFeedbackRecord],
    summary="List all staff adjustment feedback records and trace eval pairs for this deal",
)
async def get_staff_feedback(investment_id: str):
    return staff_feedback_eval_service.get_staff_edits(investment_id)


@router.post(
    "/investments/verify-artifact",
    response_model=ArtifactComplianceReport,
    summary="Execute dual-layer edge verification on an output artifact (PII, SSN, wire details, and SEC promissory returns)",
)
async def verify_output_artifact(req: VerifyArtifactRequest):
    return artifact_verifier_service.verify_artifact(req.artifact_name, req.content)


@router.get(
    "/investments/{investment_id}/hidden-fees",
    response_model=HiddenFeeScanResponse,
    summary="Scan data room agreements for hidden monitoring fees, non-fiduciary retainers, and liquidation ratchets",
)
async def scan_hidden_fees_and_conflicts(investment_id: str):
    return fee_and_conflict_scanner.scan_investment_documents(investment_id)


@router.get(
    "/operational-knowledge",
    response_model=List[OperationalKnowledgeItem],
    summary="List curated operational knowledge base guideline files that agents cite in due diligence",
)
@router.get(
    "/firm/operational-knowledge",
    response_model=List[OperationalKnowledgeItem],
    include_in_schema=False,
)
async def list_operational_knowledge():
    return operational_knowledge_service.list_knowledge_items()


@router.put(
    "/operational-knowledge/{item_id}",
    response_model=OperationalKnowledgeItem,
    summary="Update an operational knowledge guideline file directly from the product UI",
)
@router.put(
    "/firm/operational-knowledge/{item_id}",
    response_model=OperationalKnowledgeItem,
    include_in_schema=False,
)
async def update_operational_knowledge(
    item_id: str,
    title: str,
    content_markdown: str,
    editor: Optional[str] = "Deal Lead",
):
    updated = operational_knowledge_service.update_knowledge_item(
        item_id, title, content_markdown, editor
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return updated


@router.get(
    "/evals/arca/run",
    response_model=ArcaEvalScorecard,
    summary="Execute the complete Arca AI-Native Firm Benchmark & Golden Evaluation Suite",
)
async def run_arca_eval_suite():
    return arca_eval_runner.run_all_evals()
