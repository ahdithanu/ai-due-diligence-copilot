from typing import Optional, List
import logging

from backend.domain.schemas import DiligenceState, DiligenceStatus, MaterialityLevel, ClaimType
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 3
CONFIDENCE_THRESHOLD = 0.60

class HumanReviewGateNode(BaseNode):
    """
    Human Review Gate Node that checks interrupt conditions:
    1. Material contradictions (HIGH or CRITICAL materiality)
    2. Low confidence (< 0.60)
    3. Max iterations reached (node iteration count >= max_iterations)
    4. Unverified assumptions (assumptions present or ClaimType.ASSUMPTION)
    
    If any condition is triggered, updates state.human_review_required = True,
    sets human_review_reasons, and sets state.status = DiligenceStatus.HUMAN_REVIEW.
    """

    def __init__(
        self,
        name: str = "HumanReviewGateNode",
        description: str = "Human Review Gate Node for checking interrupt conditions",
        model_adapter: Optional[ModelAdapter] = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        confidence_threshold: float = CONFIDENCE_THRESHOLD
    ):
        super().__init__(name=name, description=description, model_adapter=model_adapter)
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold

    async def process(self, state: DiligenceState) -> DiligenceState:
        reasons: List[str] = list(state.human_review_reasons)

        # 1. Material Contradictions
        for c in state.contradictions:
            if c.status != "RESOLVED" and c.materiality in [MaterialityLevel.CRITICAL, MaterialityLevel.HIGH]:
                mat_val = c.materiality.value if hasattr(c.materiality, 'value') else c.materiality
                reason_msg = f"Material contradiction detected: {c.description} (Materiality: {mat_val})"
                if reason_msg not in reasons:
                    reasons.append(reason_msg)

        # 2. Low Confidence (< 0.60)
        if state.confidence_score is not None and state.confidence_score < self.confidence_threshold:
            reason_msg = f"Overall confidence score ({state.confidence_score:.2f}) is below threshold of {self.confidence_threshold:.2f}."
            if reason_msg not in reasons:
                reasons.append(reason_msg)

        # 3. Max Iterations Reached
        for node_name, count in state.iteration_counts.items():
            if count >= self.max_iterations:
                reason_msg = f"Max iteration limit ({self.max_iterations}) reached for node '{node_name}'."
                if reason_msg not in reasons:
                    reasons.append(reason_msg)

        # 4. Unverified Assumptions
        if state.assumptions:
            reason_msg = f"Unverified assumptions present in state ({len(state.assumptions)} assumptions)."
            if reason_msg not in reasons:
                reasons.append(reason_msg)
        else:
            assumption_claims_count = 0
            for domain, analysis in state.specialist_analyses.items():
                for claim in analysis.claims:
                    if claim.claim_type == ClaimType.ASSUMPTION:
                        assumption_claims_count += 1
            if assumption_claims_count > 0:
                reason_msg = f"Unverified assumption claims present in specialist analyses ({assumption_claims_count} assumptions)."
                if reason_msg not in reasons:
                    reasons.append(reason_msg)

        # If any reasons exist or human_review_required was already set
        if reasons or state.human_review_required:
            state.human_review_required = True
            state.human_review_reasons = reasons
            state.status = DiligenceStatus.HUMAN_REVIEW
            logger.info(f"HumanReviewGateNode: Human review required with {len(reasons)} reasons.")

        return state
