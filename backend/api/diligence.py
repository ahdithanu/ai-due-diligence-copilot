from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import InvestmentModel, ExecutionLogModel, GraphCheckpointModel
from backend.domain.schemas import (
    DiligenceState, DiligenceStatus, ExecutionLogEntry, AgentEvaluationResult, EvidenceRecord,
    ExecutionState, CheckpointRecord
)
from backend.engine.pipeline_builder import build_full_diligence_graph
from backend.engine.model_adapter import MockModelAdapter

router = APIRouter(prefix="/investments", tags=["Diligence Engine"])

class ResumeDiligenceRequest(BaseModel):
    action: str = Field(description="Action to take: APPROVE, REJECT, ADD_EVIDENCE")
    human_feedback: Optional[str] = None
    new_evidence: Optional[List[Dict[str, Any]]] = None

class RerunDiligenceRequest(BaseModel):
    from_node: Optional[str] = None
    domain: Optional[str] = "Financial"

@router.post("/{investment_id}/diligence/start", response_model=DiligenceState)
async def start_diligence_execution(
    investment_id: str,
    domain: str = "Financial",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    # Instantiate mock model adapter and full 17-node diligence graph engine
    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    # Run state machine graph with DB persistence enabled
    final_state = await graph.run(state, db_session=db)

    return final_state


@router.get("/{investment_id}/diligence/stream")
async def stream_diligence_execution(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    return StreamingResponse(
        graph.run_stream(state, db_session=db),
        media_type="text/event-stream"
    )



@router.post("/{investment_id}/diligence/resume", response_model=DiligenceState)
async def resume_diligence_execution(
    investment_id: str,
    req: ResumeDiligenceRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    action_upper = req.action.upper()
    if action_upper not in ["APPROVE", "REJECT", "ADD_EVIDENCE"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be APPROVE, REJECT, or ADD_EVIDENCE")

    # Clear human review flag
    state.human_review_required = False

    # Process new evidence if supplied
    added_ev_count = 0
    if action_upper == "ADD_EVIDENCE" and req.new_evidence:
        for ev_data in req.new_evidence:
            ev_record = EvidenceRecord(
                id=ev_data.get("id") or str(uuid.uuid4()),
                document_id=ev_data.get("document_id", "human-submitted"),
                chunk_id=ev_data.get("chunk_id", "human-chunk"),
                content=ev_data.get("content", ""),
                page_number=ev_data.get("page_number"),
                section_title=ev_data.get("section_title", "Human Feedback Evidence"),
                confidence=float(ev_data.get("confidence", 1.0)),
                claim_type=ev_data.get("claim_type", "FACT"),
                metadata=ev_data.get("metadata", {"source": "human_review_resume"})
            )
            state.evidence_records.append(ev_record)
            added_ev_count += 1

    # Record human decision in execution history
    decision_log = ExecutionLogEntry(
        execution_id=str(uuid.uuid4()),
        node_name="HumanReviewGateNode",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="COMPLETED",
        input_summary={
            "action": action_upper,
            "human_feedback": req.human_feedback,
            "new_evidence_count": added_ev_count
        },
        output_summary={
            "result": "RESUMED" if action_upper != "REJECT" else "REJECTED",
            "feedback_processed": bool(req.human_feedback)
        }
    )
    state.execution_history.append(decision_log)

    if action_upper == "REJECT":
        state.status = DiligenceStatus.FAILED
        inv.status = state.status.value
        inv.state_snapshot_json = state.model_dump(mode="json")
        await db.commit()
        return state

    # Resume graph execution for APPROVE or ADD_EVIDENCE
    state.status = DiligenceStatus.SPECIALIST_DILIGENCE
    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    final_state = await graph.run(state, db_session=db)
    return final_state


@router.post("/{investment_id}/diligence/rerun", response_model=DiligenceState)
async def rerun_diligence_execution(
    investment_id: str,
    req: RerunDiligenceRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    state.human_review_required = False

    rerun_log = ExecutionLogEntry(
        execution_id=str(uuid.uuid4()),
        node_name=req.from_node or "EntryNode",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="RUNNING",
        input_summary={"from_node": req.from_node, "domain": req.domain},
        output_summary={"action": "RERUN_TRIGGERED"}
    )
    state.execution_history.append(rerun_log)

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    start_node = req.from_node if req.from_node and req.from_node in graph.nodes else None

    final_state = await graph.run(state, db_session=db, start_node=start_node)
    return final_state



@router.get("/{investment_id}/diligence/logs", response_model=List[ExecutionLogEntry])
async def get_diligence_logs(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    stmt = select(ExecutionLogModel).where(ExecutionLogModel.investment_id == investment_id).order_by(ExecutionLogModel.start_time.asc())
    logs_result = await db.execute(stmt)
    db_logs = logs_result.scalars().all()

    logs = []
    for log in db_logs:
        eval_res = None
        if log.evaluation_result_json:
            eval_res = AgentEvaluationResult.model_validate(log.evaluation_result_json)

        logs.append(
            ExecutionLogEntry(
                execution_id=log.execution_id,
                node_name=log.node_name,
                start_time=log.start_time,
                end_time=log.end_time,
                status=log.status,
                input_summary=log.input_summary_json or {},
                output_summary=log.output_summary_json or {},
                model_name=log.model_name,
                token_usage=log.token_usage_json or {},
                evaluation_result=eval_res,
                iteration=log.iteration,
                next_edge_selected=log.next_edge_selected,
                error_message=log.error_message
            )
        )
    return logs


class ResolveConflictRequest(BaseModel):
    authoritative_evidence_id: str = Field(description="ID of authoritative evidence chosen by operator")
    resolved_value: Optional[float] = Field(default=None, description="Resolved numerical value if resolving metric contradiction")
    conflict_id: Optional[str] = None
    resolution_notes: Optional[str] = None

class RetryDiligenceRequest(BaseModel):
    failed_node: Optional[str] = None


@router.post("/{investment_id}/diligence/pause", response_model=DiligenceState)
async def pause_diligence_execution(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    state.execution_state = ExecutionState.PAUSED
    inv.state_snapshot_json = state.model_dump(mode="json")
    await db.commit()
    return state


@router.post("/{investment_id}/diligence/retry", response_model=DiligenceState)
async def retry_diligence_execution(
    investment_id: str,
    req: Optional[RetryDiligenceRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    target_node = None
    if req and req.failed_node and req.failed_node in graph.nodes:
        target_node = req.failed_node
    elif state.failure_details and state.failure_details.failed_node and state.failure_details.failed_node in graph.nodes:
        target_node = state.failure_details.failed_node
    elif state.checkpoint_history:
        valid_cps = [cp.node_id for cp in state.checkpoint_history if cp.node_id in graph.nodes]
        if valid_cps:
            target_node = valid_cps[-1]

    state.failure_details = None
    state.human_review_required = False
    state.human_review_reasons = []
    state.execution_state = ExecutionState.RUNNING

    final_state = await graph.run(state, db_session=db, start_node=target_node)
    return final_state


@router.post("/{investment_id}/diligence/resolve_conflict", response_model=DiligenceState)
async def resolve_evidence_conflict(
    investment_id: str,
    req: ResolveConflictRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    else:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )

    # 1. Update authoritative evidence record & update metric values if resolved_value supplied
    auth_ev = None
    for ev in state.evidence_records:
        if ev.id == req.authoritative_evidence_id:
            auth_ev = ev
            ev.confidence = 1.0
            ev.metadata["authoritative"] = True
            if req.resolved_value is not None:
                ev.metadata["resolved_value"] = req.resolved_value

    if req.resolved_value is not None:
        for fm in state.financial_metrics:
            if auth_ev and auth_ev.id in fm.input_evidence_ids:
                fm.value = req.resolved_value
            elif req.authoritative_evidence_id in [ev.id for ev in state.evidence_records]:
                fm.value = req.resolved_value

    # 2. Mark contradictions as RESOLVED
    for contradiction in state.contradictions:
        if req.conflict_id and contradiction.id == req.conflict_id:
            contradiction.status = "RESOLVED"
        elif not req.conflict_id:
            contradiction.status = "RESOLVED"

    # 3. Clear failure state & human review requirements
    state.failure_details = None
    state.human_review_required = False
    state.human_review_reasons = []
    state.execution_state = ExecutionState.RUNNING
    state.status = DiligenceStatus.SPECIALIST_DILIGENCE

    res_log = ExecutionLogEntry(
        execution_id=str(uuid.uuid4()),
        node_name="OperatorConflictResolverNode",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="COMPLETED",
        input_summary={
            "authoritative_evidence_id": req.authoritative_evidence_id,
            "resolved_value": req.resolved_value,
            "conflict_id": req.conflict_id,
            "resolution_notes": req.resolution_notes
        },
        output_summary={"resolution": "AUTHORITATIVE_EVIDENCE_SELECTED"}
    )
    state.execution_history.append(res_log)

    # Find starting node from last valid checkpoint
    start_node = None
    if state.checkpoint_history:
        valid_cps = [cp for cp in state.checkpoint_history if cp.status != ExecutionState.FAILED]
        if valid_cps:
            start_node = valid_cps[-1].node_id
        else:
            start_node = state.checkpoint_history[-1].node_id

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)
    final_state = await graph.run(state, db_session=db, start_node=start_node)
    return final_state


@router.get("/{investment_id}/diligence/checkpoints", response_model=List[CheckpointRecord])
async def get_diligence_checkpoints(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    stmt = select(GraphCheckpointModel).where(GraphCheckpointModel.investment_id == investment_id).order_by(GraphCheckpointModel.timestamp.asc())
    check_result = await db.execute(stmt)
    db_checkpoints = check_result.scalars().all()

    checkpoints = []
    for cp in db_checkpoints:
        checkpoints.append(
            CheckpointRecord(
                checkpoint_id=cp.id,
                execution_id=cp.execution_id,
                deployment_id=cp.deployment_id,
                investment_id=cp.investment_id,
                node_id=cp.node_id,
                graph_state_version=cp.graph_state_version,
                iteration_count=cp.iteration_count,
                evaluation_results=cp.evaluation_results_json or {},
                routing_decision=cp.routing_decision,
                timestamp=cp.timestamp,
                status=ExecutionState(cp.status) if cp.status in ExecutionState.__members__ else ExecutionState.RUNNING
            )
        )

    if not checkpoints and inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
        return state.checkpoint_history

    return checkpoints



