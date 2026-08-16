from typing import Optional, List, Dict, Any, Callable
import logging

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    SpecialistAnalysis,
    AgentEvaluationResult,
    ClaimNode,
    ClaimType,
    MaterialityLevel
)
from backend.engine.model_adapter import ModelAdapter
from backend.engine.node import BaseNode
from backend.engine.graph import GraphEngine, END

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 0.8
DEFAULT_MAX_ITERATIONS = 3

class AnalystGeneratorNode(BaseNode):
    """
    Analyst Generator Node in the Generate-Critique-Judge-Revise loop.
    Generates domain analysis or revises previous analysis based on Critic feedback.
    """

    def __init__(self, domain: str = "Financial", model_adapter: Optional[ModelAdapter] = None):
        super().__init__(name=f"{domain}AnalystGenerator", description=f"Generates/revises {domain} analysis", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        # Check if previous evaluation gave critique feedback
        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        current_iteration = state.iteration_counts.get(self.name, 1)

        # Build prompt incorporating feedback if available
        prompt = (
            f"Generate diligence analysis for company '{state.company_name}' in domain '{self.domain}'.\n"
            f"Evidence count: {len(state.evidence_records)}.\n"
        )
        if previous_feedback:
            prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

        if self.model_adapter:
            analysis = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if not isinstance(analysis, SpecialistAnalysis):
                # Fallback if text was returned
                analysis = SpecialistAnalysis(
                    domain=self.domain,
                    summary=str(analysis),
                    confidence_score=0.85
                )
        else:
            # Default fallback analysis if no model adapter attached
            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=f"Analysis for {state.company_name} in {self.domain} domain.",
                claims=[
                    ClaimNode(
                        text=f"Sample claim for {self.domain}",
                        claim_type=ClaimType.FACT,
                        materiality=MaterialityLevel.MEDIUM
                    )
                ],
                confidence_score=0.85
            )

        analysis.domain = self.domain
        analysis.iteration_count = current_iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class CriticEvaluatorNode(BaseNode):
    """
    Critic Evaluator Node in the Generate-Critique-Judge-Revise loop.
    Evaluates the Specialist Analysis for evidence coverage, logical consistency, correctness, etc.
    """

    def __init__(self, target_analyst_node_name: str, domain: str = "Financial", model_adapter: Optional[ModelAdapter] = None, score_threshold: float = SCORE_THRESHOLD):
        super().__init__(name=f"{domain}CriticEvaluator", description=f"Evaluates {domain} analysis output", model_adapter=model_adapter)
        self.target_analyst_node_name = target_analyst_node_name
        self.domain = domain
        self.score_threshold = score_threshold

    async def process(self, state: DiligenceState) -> DiligenceState:
        analysis = state.specialist_analyses.get(self.domain)
        
        prompt = (
            f"Evaluate the following {self.domain} analysis:\n"
            f"Summary: {analysis.summary if analysis else 'None'}\n"
            f"Claims count: {len(analysis.claims) if analysis else 0}\n"
            f"Score threshold required: {self.score_threshold}"
        )

        if self.model_adapter:
            eval_result = await self.model_adapter.generate(
                prompt=prompt,
                response_model=AgentEvaluationResult
            )
            if not isinstance(eval_result, AgentEvaluationResult):
                eval_result = AgentEvaluationResult(
                    evaluator_name=self.name,
                    target_node=self.target_analyst_node_name,
                    overall_pass=True,
                    evidence_coverage_score=0.85
                )
        else:
            eval_result = AgentEvaluationResult(
                evaluator_name=self.name,
                target_node=self.target_analyst_node_name,
                evidence_coverage_score=0.85,
                citation_correctness_score=0.85,
                logical_consistency_score=0.85,
                financial_correctness_score=0.85,
                completeness_score=0.85,
                overall_pass=True
            )

        eval_result.evaluator_name = self.name
        eval_result.target_node = self.target_analyst_node_name

        # Recalculate overall_pass according to score threshold rules if needed
        scores = [
            eval_result.evidence_coverage_score,
            eval_result.citation_correctness_score,
            eval_result.logical_consistency_score,
            eval_result.financial_correctness_score,
            eval_result.completeness_score
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # If overall_pass wasn't set by model adapter or needs enforcement
        if min(scores) < self.score_threshold or avg_score < self.score_threshold:
            eval_result.overall_pass = False
            if not eval_result.critique_feedback:
                eval_result.critique_feedback.append(
                    f"Sub-score fell below threshold {self.score_threshold} (min score: {min(scores):.2f}, avg: {avg_score:.2f})."
                )
        else:
            eval_result.overall_pass = True

        state.evaluations.append(eval_result)

        if analysis:
            analysis.passed_evaluation = eval_result.overall_pass

        return state


def analyst_critic_judge_condition(
    state: DiligenceState,
    target_analyst_node_name: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS
) -> str:
    """
    Conditional routing function for the Analyst-Critic loop.
    Returns:
    - 'passed': analysis passed evaluation.
    - 'revise': evaluation failed, iteration count < max_iterations.
    - 'max_iterations_reached': evaluation failed, iteration count >= max_iterations (fallback).
    """
    if not state.evaluations:
        return "revise"

    latest_eval = state.evaluations[-1]
    if latest_eval.overall_pass:
        return "passed"

    current_iterations = state.iteration_counts.get(target_analyst_node_name, 0)
    if current_iterations < max_iterations:
        return "revise"
    else:
        # Max iterations reached: trigger fallback behavior
        state.human_review_required = True
        reason = f"Max iteration limit ({max_iterations}) reached for {target_analyst_node_name} without passing critique."
        if reason not in state.human_review_reasons:
            state.human_review_reasons.append(reason)
        state.status = DiligenceStatus.HUMAN_REVIEW
        return "max_iterations_reached"


def build_analyst_critic_graph(
    domain: str = "Financial",
    model_adapter: Optional[ModelAdapter] = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    score_threshold: float = SCORE_THRESHOLD
) -> GraphEngine:
    """
    Helper factory to assemble a complete Analyst-Critic Generate-Critique-Judge-Revise Graph.
    """
    analyst_node = AnalystGeneratorNode(domain=domain, model_adapter=model_adapter)
    critic_node = CriticEvaluatorNode(
        target_analyst_node_name=analyst_node.name,
        domain=domain,
        model_adapter=model_adapter,
        score_threshold=score_threshold
    )

    graph = GraphEngine(name=f"{domain}_analyst_critic_graph")
    graph.add_node(analyst_node.name, analyst_node)
    graph.add_node(critic_node.name, critic_node)

    graph.add_edge(analyst_node.name, critic_node.name)

    condition_fn = lambda st: analyst_critic_judge_condition(
        st,
        target_analyst_node_name=analyst_node.name,
        max_iterations=max_iterations
    )

    graph.add_conditional_edges(
        critic_node.name,
        condition_fn,
        path_map={
            "revise": analyst_node.name,
            "passed": END,
            "max_iterations_reached": END
        }
    )

    graph.set_entry_point(analyst_node.name)
    return graph
