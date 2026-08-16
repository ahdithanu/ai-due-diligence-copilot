from typing import Dict, Any, Callable, Optional, Union, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json
import time
import uuid
from datetime import datetime, timezone

from backend.domain.schemas import (
    DiligenceState, DiligenceStatus, ExecutionLogEntry, ExecutionState,
    FailureDetails, CheckpointRecord
)
from backend.engine.node import BaseNode
from backend.db.models import (
    InvestmentModel, ExecutionLogModel, FinancialMetricModel,
    InvestmentMemoModel, GraphCheckpointModel, ExecutionFailureModel
)

logger = logging.getLogger(__name__)

END = "__end__"

class ConditionalEdge:
    def __init__(self, condition_fn: Callable[[DiligenceState], str], path_map: Optional[Dict[str, str]] = None):
        self.condition_fn = condition_fn
        self.path_map = path_map or {}

    def resolve(self, state: DiligenceState) -> str:
        key = self.condition_fn(state)
        return self.path_map.get(key, key)


class GraphEngine:
    """
    State machine graph engine supporting node execution, conditional edges,
    loop state retention, checkpoint persistence, execution failure recovery, and async persistence.
    """

    def __init__(self, name: str = "diligence_graph"):
        self.name = name
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, ConditionalEdge] = {}
        self.entry_point: Optional[str] = None
        self.max_step_limit: int = 100

    def add_node(self, name: str, node: BaseNode) -> "GraphEngine":
        self.nodes[name] = node
        return self

    def add_edge(self, from_node: str, to_node: str) -> "GraphEngine":
        if from_node not in self.nodes:
            raise ValueError(f"From node '{from_node}' not registered in graph.")
        self.edges[from_node] = to_node
        return self

    def add_conditional_edges(
        self,
        from_node: str,
        condition_fn: Callable[[DiligenceState], str],
        path_map: Optional[Dict[str, str]] = None
    ) -> "GraphEngine":
        if from_node not in self.nodes:
            raise ValueError(f"From node '{from_node}' not registered in graph.")
        self.conditional_edges[from_node] = ConditionalEdge(condition_fn, path_map)
        return self

    def set_entry_point(self, name: str) -> "GraphEngine":
        if name not in self.nodes:
            raise ValueError(f"Entry point node '{name}' not registered in graph.")
        self.entry_point = name
        return self

    def _apply_deployment_config_policies(self, state: DiligenceState, current_node_name: str, iteration: int):
        """
        Inspects state.deployment_config for evaluation thresholds (min_quality_score),
        strategy thresholds, and human escalation rules. Updates state accordingly.
        """
        if not state.deployment_config:
            return

        config = state.deployment_config
        eval_thresholds = config.evaluation_thresholds or {}
        min_quality = float(eval_thresholds.get("min_quality_score", 0.85))
        max_iters = float(eval_thresholds.get("max_iterations", 3.0))

        # 1. Audit latest evaluation results for quality score threshold
        if state.evaluations:
            matching_evals = [e for e in state.evaluations if e.target_node == current_node_name]
            if matching_evals:
                latest_eval = matching_evals[-1]
                sub_scores = [
                    latest_eval.evidence_coverage_score,
                    latest_eval.citation_correctness_score,
                    latest_eval.logical_consistency_score,
                    latest_eval.financial_correctness_score,
                    latest_eval.completeness_score
                ]
                quality_score = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
                if quality_score < min_quality:
                    latest_eval.overall_pass = False
                    if iteration >= max_iters:
                        state.human_review_required = True
                        reason = f"Node '{current_node_name}' evaluation quality score ({quality_score:.2f}) below threshold ({min_quality}) after {iteration} iterations."
                        if reason not in state.human_review_reasons:
                            state.human_review_reasons.append(reason)

        # 2. Check escalation rules & strategy thresholds
        rules = config.human_escalation_rules or []
        thresholds = config.financial_thresholds or {}

        # Contradictions rule
        if "critical_contradiction_detected" in rules or "unresolved_contradictions" in rules:
            open_crit = [c for c in state.contradictions if c.status == "OPEN" and c.materiality in ["CRITICAL", "HIGH"]]
            if open_crit:
                state.human_review_required = True
                reason = f"Material contradiction detected: {open_crit[0].description}"
                if reason not in state.human_review_reasons:
                    state.human_review_reasons.append(reason)

        # Financial thresholds rules
        for fm in state.financial_metrics:
            name_lower = fm.metric_name.lower()
            if ("gross_margin" in name_lower or fm.metric_name == "Gross_Margin") and "min_gross_margin" in thresholds:
                t_val = thresholds["min_gross_margin"]
                val_pct = fm.value * 100.0 if fm.value <= 1.0 and t_val > 1.0 else fm.value
                t_pct = t_val if t_val > 1.0 else t_val * 100.0
                if val_pct < t_pct and "gross_margin_below_threshold" in rules:
                    state.human_review_required = True
                    reason = f"Gross margin ({val_pct:.1f}%) below strategy threshold ({t_pct:.1f}%)"
                    if reason not in state.human_review_reasons:
                        state.human_review_reasons.append(reason)

            if ("nrr" in name_lower or fm.metric_name == "Net_Revenue_Retention") and "min_nrr_pct" in thresholds:
                t_val = thresholds["min_nrr_pct"]
                if fm.value < t_val and ("nrr_below_100" in rules or "nrr_below_threshold" in rules):
                    state.human_review_required = True
                    reason = f"Net Revenue Retention ({fm.value:.1f}%) below strategy threshold ({t_val:.1f}%)"
                    if reason not in state.human_review_reasons:
                        state.human_review_reasons.append(reason)

            if ("ebitda" in name_lower or fm.metric_name == "EBITDA_Margin") and "min_ebitda_margin_pct" in thresholds:
                t_val = thresholds["min_ebitda_margin_pct"]
                val_ratio = fm.value / 100.0 if fm.value > 1.0 and abs(t_val) <= 1.0 else fm.value
                t_ratio = t_val if abs(t_val) <= 1.0 else t_val / 100.0
                if val_ratio < t_ratio and "negative_ebitda" in rules:
                    state.human_review_required = True
                    reason = f"EBITDA margin ({val_ratio:.2f}) below strategy threshold ({t_ratio:.2f})"
                    if reason not in state.human_review_reasons:
                        state.human_review_reasons.append(reason)

        if state.human_review_required:
            state.execution_state = ExecutionState.WAITING_FOR_HUMAN
            state.status = DiligenceStatus.HUMAN_REVIEW

    async def run(
        self,
        initial_state: DiligenceState,
        db_session: Optional[AsyncSession] = None,
        start_node: Optional[str] = None
    ) -> DiligenceState:
        """
        Execute the graph state machine starting from entry_point or start_node.
        """
        entry = start_node or self.entry_point
        if not entry:
            raise ValueError("Graph entry point is not set.")

        state = initial_state
        if state.execution_state in [ExecutionState.FAILED, ExecutionState.PAUSED]:
            state.execution_state = ExecutionState.RUNNING

        current_node_name = entry
        step_count = 0

        while current_node_name != END and step_count < self.max_step_limit:
            step_count += 1
            node = self.nodes.get(current_node_name)
            if not node:
                raise RuntimeError(f"Node '{current_node_name}' referenced but not found in graph.")

            iteration = state.iteration_counts.get(current_node_name, 0)
            state.iteration_counts[current_node_name] = iteration + 1

            # Execute node with error handling
            logger.info(f"Executing graph node '{current_node_name}' (iteration {iteration + 1})")
            try:
                state = await node.execute(state, iteration=iteration)
            except Exception as e:
                logger.error(f"Execution error in node '{current_node_name}': {e}", exc_info=True)
                state.execution_state = ExecutionState.FAILED
                state.status = DiligenceStatus.FAILED

                last_cp_id = state.checkpoint_history[-1].checkpoint_id if state.checkpoint_history else None

                state.failure_details = FailureDetails(
                    failed_node=current_node_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retryable=True,
                    last_successful_checkpoint_id=last_cp_id,
                    suggested_recovery_action=f"Retry execution from node '{current_node_name}' or checkpoint '{last_cp_id}'",
                    affected_artifacts=[]
                )

                if db_session is not None:
                    await self._persist_failure_and_checkpoint(state, current_node_name, e, db_session)
                break

            # Apply deployment policies (evaluation thresholds, escalation rules)
            self._apply_deployment_config_policies(state, current_node_name, iteration + 1)

            # Determine next node via conditional edge or normal edge
            next_node = END
            if current_node_name in self.conditional_edges:
                cond_edge = self.conditional_edges[current_node_name]
                next_node = cond_edge.resolve(state)
            elif current_node_name in self.edges:
                next_node = self.edges[current_node_name]

            # Update latest execution log with next edge selected
            if state.execution_history:
                state.execution_history[-1].next_edge_selected = next_node

            # Record CheckpointRecord in state
            cp_id = str(uuid.uuid4())
            exec_id = state.execution_history[-1].execution_id if state.execution_history else str(uuid.uuid4())
            dep_id = state.deployment_id or (state.deployment_config.deployment_id if state.deployment_config else "default")

            eval_summary = None
            if state.execution_history and state.execution_history[-1].evaluation_result:
                eval_summary = state.execution_history[-1].evaluation_result.model_dump(mode="json")
            elif state.evaluations:
                matching_evals = [ev for ev in state.evaluations if ev.target_node == current_node_name]
                if matching_evals:
                    eval_summary = matching_evals[-1].model_dump(mode="json")

            checkpoint_rec = CheckpointRecord(
                checkpoint_id=cp_id,
                execution_id=exec_id,
                deployment_id=dep_id,
                investment_id=state.investment_id,
                node_id=current_node_name,
                graph_state_version=1,
                iteration_count=iteration + 1,
                evaluation_results=eval_summary or {},
                routing_decision=next_node,
                status=state.execution_state,
                timestamp=datetime.now(timezone.utc)
            )
            state.checkpoint_history.append(checkpoint_rec)

            # Async DB persistence if db_session is provided
            if db_session is not None:
                await self._persist_state_and_checkpoint(state, checkpoint_rec, db_session)

            # Check if human review is required
            if state.human_review_required or state.status == DiligenceStatus.HUMAN_REVIEW or state.execution_state == ExecutionState.WAITING_FOR_HUMAN:
                logger.info(f"Human review required. Interrupting graph execution after node '{current_node_name}'.")
                state.execution_state = ExecutionState.WAITING_FOR_HUMAN
                state.status = DiligenceStatus.HUMAN_REVIEW
                break

            current_node_name = next_node

        if step_count >= self.max_step_limit:
            logger.warning(f"Graph execution hit step limit of {self.max_step_limit}")

        if current_node_name == END and state.execution_state == ExecutionState.RUNNING:
            state.execution_state = ExecutionState.COMPLETED

        return state

    async def run_stream(
        self,
        initial_state: DiligenceState,
        db_session: Optional[AsyncSession] = None,
        start_node: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute the graph state machine starting from entry_point or start_node,
        yielding Server-Sent Events (SSE) JSON lines as nodes begin and complete execution.
        """
        entry = start_node or self.entry_point
        if not entry:
            raise ValueError("Graph entry point is not set.")

        state = initial_state
        if state.execution_state in [ExecutionState.FAILED, ExecutionState.PAUSED]:
            state.execution_state = ExecutionState.RUNNING

        current_node_name = entry
        step_count = 0

        while current_node_name != END and step_count < self.max_step_limit:
            step_count += 1
            node = self.nodes.get(current_node_name)
            if not node:
                raise RuntimeError(f"Node '{current_node_name}' referenced but not found in graph.")

            iteration = state.iteration_counts.get(current_node_name, 0)
            state.iteration_counts[current_node_name] = iteration + 1

            start_evt = {
                "event": "node_start",
                "node": current_node_name,
                "iteration": iteration + 1
            }
            yield f"data: {json.dumps(start_evt)}\n\n"

            start_time = time.perf_counter()
            logger.info(f"Executing graph node '{current_node_name}' (iteration {iteration + 1})")
            try:
                state = await node.execute(state, iteration=iteration)
            except Exception as e:
                logger.error(f"Execution error in node '{current_node_name}': {e}", exc_info=True)
                state.execution_state = ExecutionState.FAILED
                state.status = DiligenceStatus.FAILED

                last_cp_id = state.checkpoint_history[-1].checkpoint_id if state.checkpoint_history else None

                state.failure_details = FailureDetails(
                    failed_node=current_node_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retryable=True,
                    last_successful_checkpoint_id=last_cp_id,
                    suggested_recovery_action=f"Retry execution from node '{current_node_name}' or checkpoint '{last_cp_id}'",
                    affected_artifacts=[]
                )

                if db_session is not None:
                    await self._persist_failure_and_checkpoint(state, current_node_name, e, db_session)

                err_evt = {
                    "event": "node_error",
                    "node": current_node_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_state": ExecutionState.FAILED.value
                }
                yield f"data: {json.dumps(err_evt)}\n\n"
                break

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Apply deployment policies
            self._apply_deployment_config_policies(state, current_node_name, iteration + 1)

            eval_summary = None
            if state.execution_history and state.execution_history[-1].evaluation_result:
                eval_summary = state.execution_history[-1].evaluation_result.model_dump(mode="json")
            elif state.evaluations:
                matching_evals = [ev for ev in state.evaluations if ev.target_node == current_node_name]
                if matching_evals:
                    eval_summary = matching_evals[-1].model_dump(mode="json")

            complete_evt = {
                "event": "node_complete",
                "node": current_node_name,
                "duration_ms": duration_ms,
                "evaluation": eval_summary
            }
            yield f"data: {json.dumps(complete_evt)}\n\n"

            next_node = END
            if current_node_name in self.conditional_edges:
                cond_edge = self.conditional_edges[current_node_name]
                next_node = cond_edge.resolve(state)
            elif current_node_name in self.edges:
                next_node = self.edges[current_node_name]

            if state.execution_history:
                state.execution_history[-1].next_edge_selected = next_node

            cp_id = str(uuid.uuid4())
            exec_id = state.execution_history[-1].execution_id if state.execution_history else str(uuid.uuid4())
            dep_id = state.deployment_id or (state.deployment_config.deployment_id if state.deployment_config else "default")

            checkpoint_rec = CheckpointRecord(
                checkpoint_id=cp_id,
                execution_id=exec_id,
                deployment_id=dep_id,
                investment_id=state.investment_id,
                node_id=current_node_name,
                graph_state_version=1,
                iteration_count=iteration + 1,
                evaluation_results=eval_summary or {},
                routing_decision=next_node,
                status=state.execution_state,
                timestamp=datetime.now(timezone.utc)
            )
            state.checkpoint_history.append(checkpoint_rec)

            if db_session is not None:
                await self._persist_state_and_checkpoint(state, checkpoint_rec, db_session)

            if state.human_review_required or state.status == DiligenceStatus.HUMAN_REVIEW or state.execution_state == ExecutionState.WAITING_FOR_HUMAN:
                logger.info(f"Human review required. Interrupting graph execution after node '{current_node_name}'.")
                state.execution_state = ExecutionState.WAITING_FOR_HUMAN
                state.status = DiligenceStatus.HUMAN_REVIEW
                hr_evt = {
                    "event": "human_review",
                    "reasons": state.human_review_reasons or []
                }
                yield f"data: {json.dumps(hr_evt)}\n\n"
                break

            current_node_name = next_node

        if step_count >= self.max_step_limit:
            logger.warning(f"Graph execution hit step limit of {self.max_step_limit}")

        if current_node_name == END and state.execution_state == ExecutionState.RUNNING:
            state.execution_state = ExecutionState.COMPLETED

        status_val = state.status.value if hasattr(state.status, "value") else str(state.status)
        dc_evt = {
            "event": "diligence_complete",
            "status": status_val,
            "recommendation": state.recommendation,
            "execution_state": state.execution_state.value if hasattr(state.execution_state, "value") else str(state.execution_state)
        }
        yield f"data: {json.dumps(dc_evt)}\n\n"

    async def start_from_checkpoint(
        self,
        checkpoint_id: str,
        db_session: AsyncSession
    ) -> DiligenceState:
        """
        Restores state snapshot from target checkpoint and resumes execution
        starting from that node without re-running the full graph.
        """
        stmt = select(GraphCheckpointModel).where(GraphCheckpointModel.id == checkpoint_id)
        result = await db_session.execute(stmt)
        cp = result.scalar_one_or_none()
        if not cp or not cp.state_snapshot_json:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")

        state = DiligenceState.model_validate(cp.state_snapshot_json)
        state.execution_state = ExecutionState.RUNNING
        state.failure_details = None
        state.human_review_required = False
        state.human_review_reasons = []
        if state.status in [DiligenceStatus.HUMAN_REVIEW, DiligenceStatus.FAILED]:
            state.status = DiligenceStatus.SPECIALIST_DILIGENCE

        return await self.run(state, db_session=db_session, start_node=cp.node_id)

    async def _persist_state_and_checkpoint(
        self,
        state: DiligenceState,
        checkpoint_rec: CheckpointRecord,
        db_session: AsyncSession
    ):
        """
        Persists state snapshot to InvestmentModel, saves GraphCheckpointModel,
        and appends ExecutionLogModel asynchronously.
        """
        # Fetch investment
        result = await db_session.execute(select(InvestmentModel).where(InvestmentModel.id == state.investment_id))
        investment = result.scalar_one_or_none()
        if investment:
            investment.status = state.status.value if hasattr(state.status, "value") else str(state.status)
            investment.state_snapshot_json = state.model_dump(mode="json")

        # Sync financial metrics to FinancialMetricModel table
        fm_result = await db_session.execute(select(FinancialMetricModel.id).where(FinancialMetricModel.investment_id == state.investment_id))
        existing_fm_ids = set(fm_result.scalars().all())
        for fm in state.financial_metrics:
            if fm.id not in existing_fm_ids:
                db_fm = FinancialMetricModel(
                    id=fm.id,
                    investment_id=state.investment_id,
                    metric_name=fm.metric_name,
                    value=fm.value,
                    unit=fm.unit,
                    period=fm.period,
                    formula=fm.formula,
                    input_evidence_ids_json=fm.input_evidence_ids,
                    is_deterministic=fm.is_deterministic,
                    confidence=fm.confidence
                )
                db_session.add(db_fm)
                existing_fm_ids.add(fm.id)

        # Sync memo to InvestmentMemoModel table if available
        if state.memo_markdown:
            memo_result = await db_session.execute(select(InvestmentMemoModel).where(InvestmentMemoModel.investment_id == state.investment_id))
            db_memo = memo_result.scalar_one_or_none()
            if db_memo:
                db_memo.memo_markdown = state.memo_markdown
                db_memo.recommendation = state.recommendation or "PASS"
                db_memo.confidence_score = state.confidence_score if state.confidence_score is not None else 0.0
            else:
                db_memo = InvestmentMemoModel(
                    investment_id=state.investment_id,
                    memo_markdown=state.memo_markdown,
                    recommendation=state.recommendation or "PASS",
                    confidence_score=state.confidence_score if state.confidence_score is not None else 0.0
                )
                db_session.add(db_memo)

        # Save GraphCheckpointModel if not already added
        existing_cp = await db_session.get(GraphCheckpointModel, checkpoint_rec.checkpoint_id)
        if not existing_cp:
            db_cp = GraphCheckpointModel(
                id=checkpoint_rec.checkpoint_id,
                execution_id=checkpoint_rec.execution_id,
                deployment_id=checkpoint_rec.deployment_id,
                investment_id=state.investment_id,
                node_id=checkpoint_rec.node_id,
                graph_state_version=checkpoint_rec.graph_state_version,
                iteration_count=checkpoint_rec.iteration_count,
                state_snapshot_json=state.model_dump(mode="json"),
                evaluation_results_json=checkpoint_rec.evaluation_results,
                routing_decision=checkpoint_rec.routing_decision,
                status=checkpoint_rec.status.value if hasattr(checkpoint_rec.status, "value") else str(checkpoint_rec.status),
                timestamp=checkpoint_rec.timestamp
            )
            db_session.add(db_cp)

        # Persist execution log if log entry exists and not already added
        if state.execution_history:
            log_entry = state.execution_history[-1]
            existing_log = await db_session.get(ExecutionLogModel, log_entry.execution_id)
            if not existing_log:
                db_log = ExecutionLogModel(
                    investment_id=state.investment_id,
                    execution_id=log_entry.execution_id,
                    node_name=log_entry.node_name,
                    start_time=log_entry.start_time,
                    end_time=log_entry.end_time,
                    status=log_entry.status,
                    input_summary_json=log_entry.input_summary,
                    output_summary_json=log_entry.output_summary,
                    model_name=log_entry.model_name,
                    token_usage_json=log_entry.token_usage,
                    evaluation_result_json=log_entry.evaluation_result.model_dump(mode="json") if log_entry.evaluation_result else None,
                    iteration=log_entry.iteration,
                    next_edge_selected=log_entry.next_edge_selected,
                    error_message=log_entry.error_message
                )
                db_session.add(db_log)

        await db_session.commit()

    async def _persist_failure_and_checkpoint(
        self,
        state: DiligenceState,
        node_name: str,
        error: Exception,
        db_session: AsyncSession
    ):
        """
        Persists state snapshot, ExecutionFailureModel, and failed GraphCheckpointModel.
        """
        last_cp_id = state.checkpoint_history[-1].checkpoint_id if state.checkpoint_history else None

        result = await db_session.execute(select(InvestmentModel).where(InvestmentModel.id == state.investment_id))
        inv = result.scalar_one_or_none()
        if inv:
            inv.status = DiligenceStatus.FAILED.value
            inv.state_snapshot_json = state.model_dump(mode="json")

        execution_id = state.execution_history[-1].execution_id if state.execution_history else str(uuid.uuid4())
        db_fail = ExecutionFailureModel(
            execution_id=execution_id,
            investment_id=state.investment_id,
            failed_node=node_name,
            error_type=type(error).__name__,
            error_message=str(error),
            retryable=True,
            checkpoint_id=last_cp_id,
            suggested_recovery_action=f"Retry node execution from node '{node_name}' or checkpoint '{last_cp_id}'"
        )
        db_session.add(db_fail)

        cp_id = str(uuid.uuid4())
        deployment_id = state.deployment_id or (state.deployment_config.deployment_id if state.deployment_config else "default")

        fail_cp_rec = CheckpointRecord(
            checkpoint_id=cp_id,
            execution_id=execution_id,
            deployment_id=deployment_id,
            investment_id=state.investment_id,
            node_id=node_name,
            graph_state_version=1,
            iteration_count=state.iteration_counts.get(node_name, 1),
            evaluation_results={},
            routing_decision=END,
            status=ExecutionState.FAILED,
            timestamp=datetime.now(timezone.utc)
        )
        state.checkpoint_history.append(fail_cp_rec)

        db_cp = GraphCheckpointModel(
            id=cp_id,
            execution_id=execution_id,
            deployment_id=deployment_id,
            investment_id=state.investment_id,
            node_id=node_name,
            graph_state_version=1,
            iteration_count=state.iteration_counts.get(node_name, 1),
            state_snapshot_json=state.model_dump(mode="json"),
            evaluation_results_json={},
            routing_decision=END,
            status="FAILED",
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(db_cp)
        await db_session.commit()


