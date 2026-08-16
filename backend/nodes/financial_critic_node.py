import re
from typing import Optional, List, Set
import logging

from backend.domain.schemas import (
    DiligenceState,
    AgentEvaluationResult,
    SpecialistAnalysis,
    ClaimNode
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 0.8
TOLERANCE_PCT = 0.0001  # 0.01% tolerance (0.0001 relative)

class FinancialCriticNode(BaseNode):
    """
    Financial Critic Node that audits financial claims against deterministic calculations
    and validates evidence citations.
    """

    def __init__(
        self,
        name: str = "FinancialCritic",
        target_analyst_node_name: str = "FinancialAnalyst",
        score_threshold: float = SCORE_THRESHOLD,
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Audits financial claims against deterministic calculations and citations", model_adapter=model_adapter)
        self.target_analyst_node_name = target_analyst_node_name
        self.score_threshold = score_threshold

    async def process(self, state: DiligenceState) -> DiligenceState:
        analysis: Optional[SpecialistAnalysis] = state.specialist_analyses.get("Financial")

        critique_feedback: List[str] = []

        # Collect all valid evidence IDs in the current state
        valid_ev_ids: Set[str] = {ev.id for ev in state.evidence_records}
        for fm in state.financial_metrics:
            valid_ev_ids.update(fm.input_evidence_ids)

        if not analysis or not analysis.claims:
            eval_result = AgentEvaluationResult(
                evaluator_name=self.name,
                target_node=self.target_analyst_node_name,
                evidence_coverage_score=0.0,
                citation_correctness_score=0.0,
                logical_consistency_score=0.0,
                financial_correctness_score=0.0,
                completeness_score=0.0,
                overall_pass=False,
                critique_feedback=["No financial analysis or claims found to evaluate."]
            )
            state.evaluations.append(eval_result)
            return state

        # 1. Audit Citations
        total_claims = len(analysis.claims)
        valid_citation_claims = 0

        for claim in analysis.claims:
            if not claim.evidence_ids:
                critique_feedback.append(f"Claim '{claim.text}' lacks evidence citations.")
            else:
                invalid_ids = [eid for eid in claim.evidence_ids if eid not in valid_ev_ids]
                if invalid_ids:
                    critique_feedback.append(
                        f"Claim '{claim.text}' references invalid evidence IDs: {invalid_ids}."
                    )
                else:
                    valid_citation_claims += 1

        citation_correctness_score = valid_citation_claims / total_claims if total_claims > 0 else 0.0

        # 2. Audit Deterministic Financial Numerical Claims against state.financial_metrics
        numeric_claims_checked = 0
        numeric_claims_passed = 0

        metric_map = {fm.metric_name.lower(): fm for fm in state.financial_metrics}
        # Also map alternative names
        alias_map = {
            "arr": "arr",
            "mrr": "mrr",
            "gross margin": "gross_margin",
            "operating margin": "operating_margin",
            "ebitda margin": "ebitda_margin",
            "burn rate": "burn_rate",
            "runway": "runway",
            "nrr": "net_revenue_retention",
            "net revenue retention": "net_revenue_retention",
            "customer concentration": "customer_concentration",
            "cac": "cac",
            "ltv": "ltv",
            "ltv/cac": "ltv_cac",
            "cac payback": "cac_payback",
            "rule of 40": "rule_of_40",
            "cash conversion": "cash_conversion",
            "working capital": "working_capital",
            "revenue growth": "revenue_growth"
        }

        num_regex = re.compile(r"(-?\d+(?:\.\d+)?)")

        for claim in analysis.claims:
            claim_text_lower = claim.text.lower()
            
            # Find matching metric in claim text
            matched_metric_name = None
            for alias, canonical_name in alias_map.items():
                if alias in claim_text_lower and canonical_name in metric_map:
                    matched_metric_name = canonical_name
                    break

            if matched_metric_name:
                calc_metric = metric_map[matched_metric_name]
                numbers_in_claim = num_regex.findall(claim.text)
                
                if numbers_in_claim:
                    numeric_claims_checked += 1
                    # Parse claim values and check if any matches calculated metric within tolerance
                    passed_this_claim = False
                    for num_str in numbers_in_claim:
                        try:
                            claim_val = float(num_str)
                            if calc_metric.value != 0:
                                rel_diff = abs(claim_val - calc_metric.value) / abs(calc_metric.value)
                            else:
                                rel_diff = abs(claim_val - calc_metric.value)

                            if rel_diff <= TOLERANCE_PCT:
                                passed_this_claim = True
                                break
                        except ValueError:
                            continue

                    if passed_this_claim:
                        numeric_claims_passed += 1
                    else:
                        critique_feedback.append(
                            f"Claim '{claim.text}' numerical value does not match calculated {calc_metric.metric_name} ({calc_metric.value}) within 0.01% tolerance."
                        )

        if numeric_claims_checked > 0:
            financial_correctness_score = numeric_claims_passed / numeric_claims_checked
        else:
            financial_correctness_score = 1.0  # Pass if no numeric metric claims to verify

        # 3. Overall sub-scores and evaluation
        evidence_coverage_score = 1.0 if len(state.financial_metrics) == 0 else min(1.0, len(analysis.claims) / max(1, len(state.financial_metrics)))
        logical_consistency_score = 0.9
        completeness_score = 0.9

        scores = [
            citation_correctness_score,
            financial_correctness_score,
            evidence_coverage_score,
            logical_consistency_score,
            completeness_score
        ]

        overall_pass = (
            citation_correctness_score >= 1.0 and
            financial_correctness_score >= 1.0 and
            min(scores) >= self.score_threshold
        )

        eval_result = AgentEvaluationResult(
            evaluator_name=self.name,
            target_node=self.target_analyst_node_name,
            evidence_coverage_score=round(evidence_coverage_score, 4),
            citation_correctness_score=round(citation_correctness_score, 4),
            logical_consistency_score=round(logical_consistency_score, 4),
            financial_correctness_score=round(financial_correctness_score, 4),
            completeness_score=round(completeness_score, 4),
            overall_pass=overall_pass,
            critique_feedback=critique_feedback
        )

        state.evaluations.append(eval_result)
        analysis.passed_evaluation = overall_pass
        return state
