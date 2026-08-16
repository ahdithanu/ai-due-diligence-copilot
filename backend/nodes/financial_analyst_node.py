from typing import Optional, List
import logging

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    SpecialistAnalysis,
    ClaimNode,
    ClaimType,
    MaterialityLevel,
    FinancialMetricRecord
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter
from backend.services.financial_calculator import extract_and_calculate_metrics

logger = logging.getLogger(__name__)

class DeterministicFinancialEngineNode(BaseNode):
    """
    Computes all deterministic financial metrics from evidence records
    and appends them to state.financial_metrics.
    """

    def __init__(self, name: str = "DeterministicFinancialEngine", description: str = "Calculates deterministic financial metrics"):
        super().__init__(name=name, description=description)

    async def process(self, state: DiligenceState) -> DiligenceState:
        new_metrics: List[FinancialMetricRecord] = extract_and_calculate_metrics(state)
        
        # Deduplicate and append to state.financial_metrics
        existing_keys = {(m.metric_name, m.period, m.value) for m in state.financial_metrics}
        for metric in new_metrics:
            key = (metric.metric_name, metric.period, metric.value)
            if key not in existing_keys:
                state.financial_metrics.append(metric)
                existing_keys.add(key)

        return state


class FinancialAnalystNode(BaseNode):
    """
    Financial Analyst Node that consumes financial_metrics and evidence_records
    to generate a SpecialistAnalysis for domain="Financial".
    """

    def __init__(
        self,
        name: str = "FinancialAnalyst",
        domain: str = "Financial",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description=f"Analyzes financial data for domain {domain}", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)

        # Gather evidence IDs for valid citation lookup
        valid_ev_ids = [ev.id for ev in state.evidence_records]
        for fm in state.financial_metrics:
            valid_ev_ids.extend(fm.input_evidence_ids)
        valid_ev_ids = list(set(valid_ev_ids))

        # Check for previous critique feedback if revising
        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        strategy = ""
        thresholds = {}
        if state.deployment_config:
            strategy = (state.deployment_config.investment_strategy or "").lower()
            thresholds = state.deployment_config.financial_thresholds or {}

        is_buyout = "buyout" in strategy or "traditional" in strategy
        is_saas = not is_buyout  # Default to Growth Equity SaaS focus if not buyout

        if self.model_adapter:
            prompt = (
                f"Analyze financial metrics and evidence for company '{state.company_name}'.\n"
                f"Financial Metrics Count: {len(state.financial_metrics)}\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if is_buyout:
                prompt += "INVESTMENT STRATEGY FOCUS: Traditional Buyout. Emphasize EBITDA margin, leverage, cash conversion, working capital.\n"
            else:
                prompt += "INVESTMENT STRATEGY FOCUS: Growth Equity SaaS. Emphasize ARR growth, NRR, CAC payback, Rule of 40.\n"

            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )

            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(
                    domain=self.domain,
                    summary=str(generated),
                    confidence_score=0.9
                )
        else:
            # Deterministic default synthesis of financial metrics and evidence
            summary_parts = []
            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for fm in state.financial_metrics:
                summary_parts.append(f"{fm.metric_name} ({fm.period}): {fm.value} {fm.unit}")
                
                # Create a claim node with valid evidence IDs attached
                ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                claims.append(
                    ClaimNode(
                        text=f"{fm.metric_name} for {fm.period} is calculated at {fm.value} {fm.unit}.",
                        claim_type=ClaimType.CALCULATION,
                        evidence_ids=ev_ids,
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                    )
                )

                if is_buyout:
                    # Traditional Buyout emphasis: EBITDA margin, leverage, cash conversion, working capital
                    if fm.metric_name == "EBITDA_Margin":
                        min_ebitda = thresholds.get("min_ebitda_margin_pct", 0.15)
                        val_norm = fm.value / 100.0 if fm.value > 1.0 and abs(min_ebitda) <= 1.0 else fm.value
                        thresh_norm = min_ebitda if abs(min_ebitda) <= 1.0 else min_ebitda / 100.0
                        if val_norm >= thresh_norm:
                            strengths.append(f"Strong EBITDA margin of {fm.value} {fm.unit} in {fm.period} (Target >= {min_ebitda})")
                        else:
                            concerns.append(f"EBITDA margin of {fm.value} {fm.unit} below buyout threshold ({min_ebitda}) in {fm.period}")
                    elif fm.metric_name in ["Leverage_Ratio", "Debt_Ratio"]:
                        max_lev = thresholds.get("max_leverage_ratio", 4.0)
                        if fm.value <= max_lev:
                            strengths.append(f"Manageable leverage ratio of {fm.value} {fm.unit} in {fm.period}")
                        else:
                            concerns.append(f"High leverage ratio of {fm.value} {fm.unit} exceeding buyout max ({max_lev}) in {fm.period}")
                    elif fm.metric_name == "Cash_Conversion":
                        strengths.append(f"Cash conversion efficiency of {fm.value} {fm.unit} in {fm.period}")
                    elif fm.metric_name == "Working_Capital":
                        if fm.value > 0:
                            strengths.append(f"Positive working capital of {fm.value} {fm.unit} in {fm.period}")
                        else:
                            concerns.append(f"Working capital deficit of {fm.value} {fm.unit} in {fm.period}")
                    elif fm.metric_name in ["Gross_Margin", "Revenue_Growth"] and fm.value > 40:
                        strengths.append(f"Solid {fm.metric_name} of {fm.value} {fm.unit} in {fm.period}")
                else:
                    # Growth Equity SaaS emphasis: ARR growth, NRR, CAC payback, Rule of 40
                    if fm.metric_name in ["Gross_Margin", "Revenue_Growth", "Rule_of_40", "Net_Revenue_Retention", "ARR_Growth"] and fm.value > 30:
                        strengths.append(f"Strong {fm.metric_name} of {fm.value} {fm.unit} in {fm.period}")
                    if fm.metric_name == "CAC_Payback" and fm.value <= thresholds.get("max_cac_payback_months", 18):
                        strengths.append(f"Fast CAC payback period of {fm.value} months in {fm.period}")
                    elif fm.metric_name == "CAC_Payback" and fm.value > thresholds.get("max_cac_payback_months", 18):
                        concerns.append(f"CAC payback period of {fm.value} months exceeds target ({thresholds.get('max_cac_payback_months', 18)} months)")
                    if fm.metric_name in ["Runway"] and fm.value < 12:
                        concerns.append(f"Limited Runway of {fm.value} months in {fm.period}")

            # If evidence records exist, add factual claim
            if state.evidence_records:
                first_ev = state.evidence_records[0]
                claims.append(
                    ClaimNode(
                        text=f"Extracted evidence state: {first_ev.content}",
                        claim_type=first_ev.claim_type,
                        evidence_ids=[first_ev.id],
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Directly extracted from document chunk."
                    )
                )

            strat_name = "Traditional Buyout" if is_buyout else "Growth Equity SaaS"
            strat_focus = "EBITDA margin, leverage, cash conversion, working capital" if is_buyout else "ARR growth, NRR, CAC payback, Rule of 40"
            summary_str = f"Financial analysis for {state.company_name} (Strategy: {strat_name}, Focus: {strat_focus}). Metrics: " + (", ".join(summary_parts) if summary_parts else "No deterministic metrics computed yet.")

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.9,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state
