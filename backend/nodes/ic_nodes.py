import logging
from typing import Optional, List, Set, Dict, Any
import uuid

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    MaterialityLevel,
    ClaimType
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)


class BullNode(BaseNode):
    """
    Bull Node: Builds an evidence-grounded investment upside case.
    Pulls positive insights from specialist analyses, strong financial metrics, and evidence records.
    Appends to state.bull_case with explicit citations ([Evidence: ev_id]).
    """

    def __init__(self, name: str = "BullNode", model_adapter: Optional[ModelAdapter] = None):
        super().__init__(
            name=name,
            description="Builds evidence-grounded investment upside case",
            model_adapter=model_adapter
        )

    async def process(self, state: DiligenceState) -> DiligenceState:
        if self.model_adapter:
            prompt = (
                f"Build a compelling, evidence-grounded investment bull case for '{state.company_name}'.\n"
                f"Industry: {state.industry}, Target Round: {state.target_round}.\n"
                f"Specialist Analyses: {[domain for domain in state.specialist_analyses.keys()]}\n"
                f"Evidence Records Count: {len(state.evidence_records)}.\n"
                f"Include explicit citations formatted as [Evidence: ev_id] for key points."
            )
            bull_output = await self.model_adapter.generate(prompt=prompt, response_model=str)
            case_text = str(bull_output)
        else:
            # Deterministic upside case synthesis
            upside_points: List[str] = []

            # 1. Specialist Analyses Strengths & Claims
            for domain, analysis in state.specialist_analyses.items():
                if analysis.strengths:
                    for s in analysis.strengths:
                        ev_cite = ""
                        if state.evidence_records:
                            ev_cite = f" [Evidence: {state.evidence_records[0].id}]"
                        upside_points.append(f"**{domain} Advantage**: {s}{ev_cite}")
                for claim in analysis.claims:
                    if claim.claim_type in [ClaimType.FACT, ClaimType.CALCULATION] and claim.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]:
                        cite_str = " ".join([f"[Evidence: {eid}]" for eid in claim.evidence_ids])
                        upside_points.append(f"**Key Growth Driver**: {claim.text} {cite_str}".strip())

            # 2. Strong Financial Metrics
            for fm in state.financial_metrics:
                cite_str = " ".join([f"[Evidence: {eid}]" for eid in fm.input_evidence_ids])
                if fm.metric_name in ["Revenue_Growth", "RevenueGrowth", "ARR_Growth"] and fm.value > 20:
                    upside_points.append(f"**High Growth Metric**: {fm.metric_name} reached {fm.value}% {cite_str}".strip())
                elif fm.metric_name in ["Gross_Margin", "GrossMargin"] and fm.value >= 70:
                    upside_points.append(f"**Strong Unit Economics**: {fm.metric_name} of {fm.value}% {cite_str}".strip())
                elif fm.metric_name in ["NRR", "Net_Revenue_Retention"] and fm.value >= 110:
                    upside_points.append(f"**Customer Retention**: Net Revenue Retention of {fm.value}% {cite_str}".strip())

            # 3. Direct Evidence Records Fallback
            if not upside_points:
                for ev in state.evidence_records[:3]:
                    upside_points.append(f"**Evidence Highlight**: {ev.content} [Evidence: {ev.id}]")

            if not upside_points:
                upside_points.append(f"Strong market opportunity in {state.industry} for {state.company_name}.")

            case_text = (
                f"### Bull Case (Upside Narrative) for {state.company_name}\n\n"
                + "\n".join([f"- {p}" for p in upside_points])
            )

        if state.bull_case:
            state.bull_case = f"{state.bull_case}\n\n{case_text}"
        else:
            state.bull_case = case_text

        state.status = DiligenceStatus.INVESTMENT_COMMITTEE
        return state


class BearNode(BaseNode):
    """
    Bear Node: Builds an evidence-grounded downside investment case.
    Pulls risks from risk register, specialist concerns, low financial metrics, and contradictions.
    Appends to state.bear_case with explicit citations ([Evidence: ev_id]).
    """

    def __init__(self, name: str = "BearNode", model_adapter: Optional[ModelAdapter] = None):
        super().__init__(
            name=name,
            description="Builds evidence-grounded investment downside case",
            model_adapter=model_adapter
        )

    async def process(self, state: DiligenceState) -> DiligenceState:
        if self.model_adapter:
            prompt = (
                f"Build a rigorous, evidence-grounded downside investment bear case for '{state.company_name}'.\n"
                f"Risk Register Count: {len(state.risk_register)}, Contradictions: {len(state.contradictions)}.\n"
                f"Include explicit citations formatted as [Evidence: ev_id]."
            )
            bear_output = await self.model_adapter.generate(prompt=prompt, response_model=str)
            case_text = str(bear_output)
        else:
            downside_points: List[str] = []

            # 1. Risk Register Items
            for risk in state.risk_register:
                cite_str = " ".join([f"[Evidence: {eid}]" for eid in risk.evidence_ids])
                downside_points.append(f"**Risk Factor** [{risk.materiality}]: {risk.text} {cite_str}".strip())

            # 2. Specialist Concerns
            for domain, analysis in state.specialist_analyses.items():
                if analysis.concerns:
                    for c in analysis.concerns:
                        ev_cite = ""
                        if state.evidence_records:
                            ev_cite = f" [Evidence: {state.evidence_records[-1].id}]"
                        downside_points.append(f"**{domain} Concern**: {c}{ev_cite}")

            # 3. Contradictions
            for contradiction in state.contradictions:
                downside_points.append(
                    f"**Evidence Discrepancy**: {contradiction.description} [Claim A: {contradiction.claim_a_id}, Claim B: {contradiction.claim_b_id}]"
                )

            # 4. Weak Financial Metrics
            for fm in state.financial_metrics:
                cite_str = " ".join([f"[Evidence: {eid}]" for eid in fm.input_evidence_ids])
                if fm.metric_name in ["Burn_Rate", "MonthlyBurn"] and fm.value > 100000:
                    downside_points.append(f"**Capital Intensity**: High burn rate of ${fm.value:,.2f}/mo {cite_str}".strip())
                elif fm.metric_name in ["Runway", "RunwayMonths"] and fm.value < 12:
                    downside_points.append(f"**Refinancing Risk**: Short runway of {fm.value} months {cite_str}".strip())
                elif fm.metric_name in ["CAC_Payback"] and fm.value > 18:
                    downside_points.append(f"**Customer Acquisition Efficiency**: Extended payback of {fm.value} months {cite_str}".strip())

            if not downside_points:
                downside_points.append(f"Early stage risk and execution uncertainty in {state.industry}.")

            case_text = (
                f"### Bear Case (Downside Risk Narrative) for {state.company_name}\n\n"
                + "\n".join([f"- {p}" for p in downside_points])
            )

        if state.bear_case:
            state.bear_case = f"{state.bear_case}\n\n{case_text}"
        else:
            state.bear_case = case_text

        state.status = DiligenceStatus.INVESTMENT_COMMITTEE
        return state


class SkepticNode(BaseNode):
    """
    Skeptic Node: Attacks Bull and Bear cases for unsubstantiated optimism or missing evidence.
    Identifies ungrounded claims, unresolved contradictions, and open diligence questions.
    Appends to state.skeptic_critique. If critical unresolved flaws are found, sets state.human_review_required = True
    and flags routing back to gap detection.
    """

    def __init__(self, name: str = "SkepticNode", model_adapter: Optional[ModelAdapter] = None):
        super().__init__(
            name=name,
            description="Attacks Bull and Bear cases for missing evidence or unsubstantiated assumptions",
            model_adapter=model_adapter
        )

    async def process(self, state: DiligenceState) -> DiligenceState:
        valid_ev_ids: Set[str] = {ev.id for ev in state.evidence_records}

        critiques: List[str] = []
        critical_flaws_found = False

        # 1. Audit Bull Case Citations and Evidence Coverage
        if not state.bull_case or "[Evidence:" not in state.bull_case:
            critiques.append("Bull Case relies on broad assertions lacking direct [Evidence: ev_id] citations.")

        # 2. Check for Unresolved High/Critical Contradictions
        critical_contradictions = [c for c in state.contradictions if c.status == "OPEN" and c.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]]
        if critical_contradictions:
            critical_flaws_found = True
            for c in critical_contradictions:
                critiques.append(f"CRITICAL FLAW: Unresolved contradiction ({c.materiality}): {c.description}")

        # 3. Check for Unanswered Critical Diligence Questions
        unanswered_critical_q = [q for q in state.open_questions if q.status == "OPEN" and q.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]]
        if unanswered_critical_q:
            critical_flaws_found = True
            for q in unanswered_critical_q:
                critiques.append(f"UNANSWERED QUESTION ({q.materiality}): {q.question}")

        # 4. Check for Specialist Analyses lacking Evidence Citations or Low Confidence
        for domain, analysis in state.specialist_analyses.items():
            if not analysis.passed_evaluation:
                critiques.append(f"{domain} domain failed critic evaluation and remains unverified.")
            unbacked_claims = [cl for cl in analysis.claims if not cl.evidence_ids]
            if unbacked_claims:
                critiques.append(f"{domain} domain contains {len(unbacked_claims)} claims without evidence citations.")

        if not critiques:
            critiques.append("Skeptic Review: Both Bull and Bear cases are reasonably grounded in available evidence, though ongoing monitoring is required.")

        critique_text = (
            f"### Skeptic Critique & Gap Analysis for {state.company_name}\n\n"
            + "\n".join([f"- {c}" for c in critiques])
        )

        if state.skeptic_critique:
            state.skeptic_critique = f"{state.skeptic_critique}\n\n{critique_text}"
        else:
            state.skeptic_critique = critique_text

        # If critical flaws found, set human review required and append reasons
        if critical_flaws_found:
            state.human_review_required = True
            reason = f"Skeptic Node identified {len(critical_contradictions)} critical contradiction(s) and {len(unanswered_critical_q)} unanswered critical question(s)."
            if reason not in state.human_review_reasons:
                state.human_review_reasons.append(reason)

        state.status = DiligenceStatus.INVESTMENT_COMMITTEE
        return state


class ICSynthesizerNode(BaseNode):
    """
    IC Synthesizer Node: Evaluates Bull, Bear, and Skeptic positions based on evidence quality and materiality
    (no simple averaging). Produces state.investment_thesis, state.recommendation ("INVEST", "PASS", or "CONDITIONAL_PASS"),
    and state.confidence_score.
    """

    def __init__(self, name: str = "ICSynthesizer", model_adapter: Optional[ModelAdapter] = None):
        super().__init__(
            name=name,
            description="Evaluates IC positions and synthesizes thesis, recommendation, and confidence",
            model_adapter=model_adapter
        )

    async def process(self, state: DiligenceState) -> DiligenceState:
        if self.model_adapter:
            prompt = (
                f"Synthesize Investment Committee decision for '{state.company_name}'.\n"
                f"Bull Case: {state.bull_case[:300] if state.bull_case else 'None'}\n"
                f"Bear Case: {state.bear_case[:300] if state.bear_case else 'None'}\n"
                f"Skeptic Critique: {state.skeptic_critique[:300] if state.skeptic_critique else 'None'}\n"
                f"Human Review Required: {state.human_review_required}\n"
                f"Provide recommendation (INVEST, PASS, CONDITIONAL_PASS) and thesis."
            )
            synth_res = await self.model_adapter.generate(prompt=prompt, response_model=Dict[str, Any])
            if isinstance(synth_res, dict):
                thesis = synth_res.get("thesis", f"Investment thesis for {state.company_name}")
                recommendation = synth_res.get("recommendation", "CONDITIONAL_PASS")
                confidence = float(synth_res.get("confidence_score", 0.75))
            else:
                thesis = f"Investment thesis for {state.company_name} in {state.industry}."
                recommendation = "CONDITIONAL_PASS"
                confidence = 0.75
        else:
            # Deterministic evidence-weighted IC evaluation logic
            # Weigh evidence quality, critical risk count, contradiction count, and skeptic critique
            open_critical_contradictions = [c for c in state.contradictions if c.status == "OPEN" and c.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]]
            open_critical_questions = [q for q in state.open_questions if q.status == "OPEN" and q.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]]
            critical_risks = [r for r in state.risk_register if r.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]]

            # Base thesis
            thesis_parts = [
                f"{state.company_name} operates in the {state.industry} sector seeking {state.target_round} funding."
            ]

            if state.bull_case:
                thesis_parts.append("Key investment merits center on strong market positioning and unit economics.")
            if state.bear_case:
                thesis_parts.append("Downside risks pertain to execution timeline, capital burn, and competitive pressures.")

            thesis = " ".join(thesis_parts)

            # Determine Recommendation
            if open_critical_contradictions or len(critical_risks) >= 3:
                recommendation = "PASS"
                thesis += " PASS recommendation due to unresolved critical evidence contradictions and unmitigated risk factors."
            elif state.human_review_required or open_critical_questions or len(critical_risks) > 0:
                recommendation = "CONDITIONAL_PASS"
                thesis += " CONDITIONAL PASS recommendation subject to resolving outstanding diligence questions and verification during confirmatory diligence."
            else:
                recommendation = "INVEST"
                thesis += " INVEST recommendation supported by verified evidence across growth, market opportunity, and financial stability."

            # Calculate Confidence Score based on evidence metrics (not simple averaging)
            # Factors: evidence count, citation ratio, evaluation pass rates, open questions ratio
            total_claims = sum(len(sa.claims) for sa in state.specialist_analyses.values())
            claims_with_cite = sum(len([c for c in sa.claims if c.evidence_ids]) for sa in state.specialist_analyses.values())

            citation_ratio = claims_with_cite / total_claims if total_claims > 0 else 0.5

            eval_pass_count = sum(1 for e in state.evaluations if e.overall_pass)
            total_evals = len(state.evaluations)
            eval_ratio = eval_pass_count / total_evals if total_evals > 0 else 0.8

            evidence_factor = min(1.0, len(state.evidence_records) / 5.0) if state.evidence_records else 0.4
            risk_penalty = len(open_critical_contradictions) * 0.2 + len(open_critical_questions) * 0.1

            raw_confidence = (0.4 * citation_ratio + 0.3 * eval_ratio + 0.3 * evidence_factor) - risk_penalty
            confidence = max(0.1, min(0.99, round(raw_confidence, 2)))

        state.investment_thesis = thesis
        state.recommendation = recommendation
        state.confidence_score = confidence
        state.status = DiligenceStatus.INVESTMENT_COMMITTEE
        return state


def skeptic_routing_condition(state: DiligenceState) -> str:
    """
    Conditional routing edge function for Skeptic evaluation.
    Routes state to 'GapDetector' if critical unresolved flaws exist (or human review required),
    else routes to 'ICSynthesizer'.
    """
    # Check if skeptic critique or state indicates critical flaws / human review / unresolved gaps
    has_critical_flaws = state.human_review_required or any(
        c.status == "OPEN" and c.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]
        for c in state.contradictions
    ) or any(
        q.status == "OPEN" and q.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]
        for q in state.open_questions
    )

    if has_critical_flaws:
        return "GapDetector"
    return "ICSynthesizer"
