import logging
import uuid
from typing import Optional, List, Set, Dict, Any

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    SpecialistAnalysis,
    ClaimNode,
    ClaimType,
    MaterialityLevel,
    EvidenceRecord
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)


def _filter_evidence_by_keywords(
    evidence_records: List[EvidenceRecord],
    keywords: List[str]
) -> List[EvidenceRecord]:
    """Helper to find evidence records matching any of the specified keywords."""
    matching: List[EvidenceRecord] = []
    for ev in evidence_records:
        content_lower = ev.content.lower()
        if any(kw in content_lower for kw in keywords):
            matching.append(ev)
    return matching


class MarketAnalystNode(BaseNode):
    """
    Market Analyst Node: Analyzes TAM/SAM/SOM, CAGR, macro tailwinds, and industry dynamics.
    Produces SpecialistAnalysis for domain="Market".
    """

    def __init__(
        self,
        name: str = "MarketAnalyst",
        domain: str = "Market",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Analyzes market size, TAM/SAM/SOM, CAGR, and industry dynamics", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        if self.model_adapter:
            prompt = (
                f"Analyze market dynamics, TAM/SAM/SOM, CAGR, and macro tailwinds for company '{state.company_name}' in industry '{state.industry}'.\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            market_keywords = ["tam", "sam", "som", "market", "cagr", "tailwind", "growth", "industry", "billion", "trillion", "segment"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, market_keywords)

            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Market data: {ev.content}",
                        claim_type=ev.claim_type,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning=f"Extracted from document section '{ev.section_title or 'General'}'"
                    )
                )
                if any(kw in ev.content.lower() for kw in ["cagr", "growth", "tailwind"]):
                    strengths.append(f"Favorable market dynamics identified: {ev.content[:100]}...")
                if any(kw in ev.content.lower() for kw in ["risk", "decline", "barrier", "slowdown"]):
                    concerns.append(f"Market headwind identified: {ev.content[:100]}...")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"The target market in {state.industry} presents expansion potential for {state.company_name}.",
                        claim_type=ClaimType.INFERENCE,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Inferred from company industry and positioning."
                    )
                )

            if not strengths:
                strengths.append(f"Operating in large and growing {state.industry} sector.")

            summary_str = f"Market Analysis for {state.company_name} in {state.industry}. Identified {len(claims)} market claims across TAM/SAM/SOM dynamics."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class CompetitiveAnalystNode(BaseNode):
    """
    Competitive Analyst Node: Evaluates competitive moat, direct/indirect competitors, market positioning.
    Produces SpecialistAnalysis for domain="Competitive".
    """

    def __init__(
        self,
        name: str = "CompetitiveAnalyst",
        domain: str = "Competitive",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Evaluates competitive moat, competitors, and market positioning", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        if self.model_adapter:
            prompt = (
                f"Analyze competitive moat, direct/indirect competitors, and market positioning for company '{state.company_name}'.\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            comp_keywords = ["competitor", "competition", "moat", "differentiator", "positioning", "alternative", "incumbent", "defensibility", "advantage"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, comp_keywords)

            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Competitive evidence: {ev.content}",
                        claim_type=ev.claim_type,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Extracted competitive information."
                    )
                )
                if any(kw in ev.content.lower() for kw in ["moat", "differentiator", "advantage", "defensible"]):
                    strengths.append(f"Competitive advantage: {ev.content[:100]}...")
                if any(kw in ev.content.lower() for kw in ["incumbent", "threat", "alternative", "pressure"]):
                    concerns.append(f"Competitive threat: {ev.content[:100]}...")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"{state.company_name} maintains a proprietary product strategy against incumbents in {state.industry}.",
                        claim_type=ClaimType.INFERENCE,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Inferred from product positioning."
                    )
                )

            if not strengths:
                strengths.append("Differentiated product architecture relative to legacy tools.")
            if not concerns:
                concerns.append("Potential margin compression if well-funded incumbents replicate core features.")

            summary_str = f"Competitive Analysis for {state.company_name}. Assessed moat, differentiation, and competitive threats across {len(claims)} claims."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class CustomerAnalystNode(BaseNode):
    """
    Customer Analyst Node: Evaluates customer profiles, concentration risk, churn, NRR, NPS.
    Produces SpecialistAnalysis for domain="Customer".
    """

    def __init__(
        self,
        name: str = "CustomerAnalyst",
        domain: str = "Customer",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Evaluates customer profiles, concentration risk, churn, NRR, and NPS", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        if self.model_adapter:
            prompt = (
                f"Analyze customer profiles, customer concentration risk, churn, NRR, and NPS for company '{state.company_name}'.\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            cust_keywords = ["customer", "client", "retention", "churn", "nrr", "nps", "concentration", "logo", "account", "enterprise"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, cust_keywords)

            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Customer evidence: {ev.content}",
                        claim_type=ev.claim_type,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Extracted customer metric/profile."
                    )
                )
                if any(kw in ev.content.lower() for kw in ["retention", "nrr", "nps", "satisfaction", "growth"]):
                    strengths.append(f"Strong customer metric: {ev.content[:100]}...")
                if any(kw in ev.content.lower() for kw in ["churn", "concentration", "risk", "loss", "decline"]):
                    concerns.append(f"Customer risk factor: {ev.content[:100]}...")

            # Also check financial metrics for customer concentration / NRR
            for fm in state.financial_metrics:
                if fm.metric_name in ["Net_Revenue_Retention", "Customer_Concentration"]:
                    ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                    claims.append(
                        ClaimNode(
                            text=f"Financial metric {fm.metric_name} ({fm.period}) is {fm.value} {fm.unit}.",
                            claim_type=ClaimType.CALCULATION,
                            evidence_ids=ev_ids,
                            materiality=MaterialityLevel.HIGH,
                            supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                        )
                    )
                    if fm.metric_name == "Net_Revenue_Retention" and fm.value >= 110:
                        strengths.append(f"High Net Revenue Retention of {fm.value}%")
                    elif fm.metric_name == "Customer_Concentration" and fm.value > 30:
                        concerns.append(f"Customer concentration risk: top customer represents {fm.value}% of revenue")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"{state.company_name} targets enterprise B2B customers in the {state.industry} sector.",
                        claim_type=ClaimType.INFERENCE,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Inferred from commercial focus."
                    )
                )

            summary_str = f"Customer Analysis for {state.company_name}. Evaluated customer profiles, retention, concentration, and churn across {len(claims)} claims."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class ProductAnalystNode(BaseNode):
    """
    Product Analyst Node: Evaluates tech stack, IP/patents, roadmap maturity, product differentiation.
    Produces SpecialistAnalysis for domain="Product".
    """

    def __init__(
        self,
        name: str = "ProductAnalyst",
        domain: str = "Product",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Evaluates tech stack, IP/patents, roadmap maturity, and product differentiation", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

        previous_feedback: List[str] = []
        if state.evaluations:
            latest_eval = state.evaluations[-1]
            if latest_eval.target_node == self.name and not latest_eval.overall_pass:
                previous_feedback = latest_eval.critique_feedback

        if self.model_adapter:
            prompt = (
                f"Analyze tech stack, IP/patents, roadmap maturity, and product differentiation for company '{state.company_name}'.\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            prod_keywords = ["product", "technology", "tech stack", "patent", "ip", "architecture", "roadmap", "feature", "api", "ai", "platform", "software"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, prod_keywords)

            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Product evidence: {ev.content}",
                        claim_type=ev.claim_type,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Extracted product/technology information."
                    )
                )
                if any(kw in ev.content.lower() for kw in ["patent", "proprietary", "ai", "architecture", "scalable"]):
                    strengths.append(f"Product technical strength: {ev.content[:100]}...")
                if any(kw in ev.content.lower() for kw in ["debt", "legacy", "vulnerability", "delay", "dependency"]):
                    concerns.append(f"Product/Technical risk: {ev.content[:100]}...")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"{state.company_name} develops proprietary software solutions for enterprise workflows.",
                        claim_type=ClaimType.INFERENCE,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Inferred from product description."
                    )
                )

            if not strengths:
                strengths.append("Modern cloud-native software architecture.")
            if not concerns:
                concerns.append("Ongoing R&D investment required to maintain technological lead.")

            summary_str = f"Product Analysis for {state.company_name}. Evaluated technology stack, IP, differentiation, and product roadmap maturity across {len(claims)} claims."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class RiskAnalystNode(BaseNode):
    """
    Risk Analyst Node: Identifies key person, regulatory, technology, market, financial risks.
    Produces SpecialistAnalysis for domain="Risk" AND appends ClaimNodes to state.risk_register.
    """

    def __init__(
        self,
        name: str = "RiskAnalyst",
        domain: str = "Risk",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Identifies key person, regulatory, tech, market, and financial risks", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

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

        if self.model_adapter:
            prompt = (
                f"Identify key person, regulatory, technology, market, and financial risks for company '{state.company_name}'.\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if is_buyout:
                prompt += "INVESTMENT STRATEGY FOCUS: Traditional Buyout. Emphasize leverage risk, debt service coverage, working capital volatility, and EBITDA margin compression.\n"
            else:
                prompt += "INVESTMENT STRATEGY FOCUS: Growth Equity SaaS. Emphasize burn rate, runway, customer churn, and ARR growth deceleration risks.\n"

            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            risk_keywords = ["risk", "regulatory", "compliance", "key person", "lock-in", "vulnerability", "dependency", "threat", "lawsuit", "exposure", "runway", "burn", "leverage", "ebitda"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, risk_keywords)

            claims: List[ClaimNode] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Identified risk factor: {ev.content}",
                        claim_type=ClaimType.FACT if ev.claim_type == ClaimType.FACT else ClaimType.INFERENCE,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Extracted risk evidence from document."
                    )
                )
                concerns.append(f"Risk: {ev.content[:100]}...")

            # Also check for financial risks based on strategy thresholds
            for fm in state.financial_metrics:
                if is_buyout:
                    if fm.metric_name in ["Leverage_Ratio", "Debt_Ratio"] and fm.value > thresholds.get("max_leverage_ratio", 4.0):
                        ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                        c = ClaimNode(
                            text=f"Financial Risk: Excessive leverage ratio of {fm.value} calculated for period {fm.period}.",
                            claim_type=ClaimType.CALCULATION,
                            evidence_ids=ev_ids,
                            materiality=MaterialityLevel.CRITICAL,
                            supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                        )
                        claims.append(c)
                        concerns.append(f"High leverage ratio of {fm.value}")
                    elif fm.metric_name == "EBITDA_Margin" and fm.value < thresholds.get("min_ebitda_margin_pct", 0.15):
                        ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                        c = ClaimNode(
                            text=f"Financial Risk: Low EBITDA margin of {fm.value} calculated for period {fm.period}.",
                            claim_type=ClaimType.CALCULATION,
                            evidence_ids=ev_ids,
                            materiality=MaterialityLevel.HIGH,
                            supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                        )
                        claims.append(c)
                        concerns.append(f"Low EBITDA margin of {fm.value}")
                else:
                    if fm.metric_name == "Runway" and fm.value < 12:
                        ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                        c = ClaimNode(
                            text=f"Financial Risk: Short runway of {fm.value} months calculated for period {fm.period}.",
                            claim_type=ClaimType.CALCULATION,
                            evidence_ids=ev_ids,
                            materiality=MaterialityLevel.CRITICAL,
                            supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                        )
                        claims.append(c)
                        concerns.append(f"Short runway of {fm.value} months")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"Key person dependency on founder/CEO and execution risk during growth phase for {state.company_name}.",
                        claim_type=ClaimType.ASSUMPTION,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Standard early-stage key person risk assessment."
                    )
                )
                concerns.append("Key person reliance on founding team.")

            strat_label = "Traditional Buyout" if is_buyout else "Growth Equity SaaS"
            summary_str = f"Risk Analysis for {state.company_name} ({strat_label} strategy). Identified {len(claims)} risk claims covering key person, regulatory, market, and financial vulnerabilities."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=[],
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis

        # CRITICAL REQUIREMENT: Append risk ClaimNodes to state.risk_register
        existing_risk_texts = {r.text for r in state.risk_register}
        for claim in analysis.claims:
            if claim.text not in existing_risk_texts:
                state.risk_register.append(claim)
                existing_risk_texts.add(claim.text)

        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state


class UnitEconomicsAnalystNode(BaseNode):
    """
    Unit Economics Analyst Node: Evaluates CAC, LTV, LTV/CAC payback, unit margin.
    Produces SpecialistAnalysis for domain="UnitEconomics".
    """

    def __init__(
        self,
        name: str = "UnitEconomicsAnalyst",
        domain: str = "UnitEconomics",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Evaluates CAC, LTV, LTV/CAC payback, and unit margin", model_adapter=model_adapter)
        self.domain = domain

    async def process(self, state: DiligenceState) -> DiligenceState:
        iteration = state.iteration_counts.get(self.name, 1)
        valid_ev_ids = [ev.id for ev in state.evidence_records]

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

        if self.model_adapter:
            prompt = (
                f"Analyze CAC, LTV, LTV/CAC ratio, payback period, and unit margin for company '{state.company_name}'.\n"
                f"Financial Metrics Count: {len(state.financial_metrics)}\n"
                f"Evidence Count: {len(state.evidence_records)}\n"
            )
            if is_buyout:
                prompt += "INVESTMENT STRATEGY FOCUS: Traditional Buyout. Emphasize margin stability, working capital, cash conversion, and debt service capacity.\n"
            else:
                prompt += "INVESTMENT STRATEGY FOCUS: Growth Equity SaaS. Emphasize CAC payback, LTV/CAC ratio, NRR, and gross margin.\n"

            if previous_feedback:
                prompt += f"CRITIQUE REVISION FEEDBACK: {'; '.join(previous_feedback)}\nPlease address these points explicitly."

            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=SpecialistAnalysis
            )
            if isinstance(generated, SpecialistAnalysis):
                analysis = generated
            else:
                analysis = SpecialistAnalysis(domain=self.domain, summary=str(generated), confidence_score=0.85)
        else:
            ue_keywords = ["cac", "ltv", "payback", "unit economics", "margin", "arpu", "cost per acquisition", "contribution margin", "ebitda", "leverage"]
            matched_evidence = _filter_evidence_by_keywords(state.evidence_records, ue_keywords)

            claims: List[ClaimNode] = []
            strengths: List[str] = []
            concerns: List[str] = []

            for ev in matched_evidence:
                claims.append(
                    ClaimNode(
                        text=f"Unit economics evidence: {ev.content}",
                        claim_type=ev.claim_type,
                        evidence_ids=[ev.id],
                        materiality=MaterialityLevel.HIGH,
                        supporting_reasoning="Extracted unit economics data."
                    )
                )

            # Check financial metrics for CAC, LTV, LTV_CAC, CAC_Payback, Gross_Margin, EBITDA_Margin
            for fm in state.financial_metrics:
                if fm.metric_name in ["CAC", "LTV", "LTV_CAC", "CAC_Payback", "Gross_Margin", "EBITDA_Margin", "Cash_Conversion", "Leverage_Ratio"]:
                    ev_ids = fm.input_evidence_ids if fm.input_evidence_ids else (valid_ev_ids[:1] if valid_ev_ids else [])
                    claims.append(
                        ClaimNode(
                            text=f"Unit metric {fm.metric_name} ({fm.period}) is {fm.value} {fm.unit}.",
                            claim_type=ClaimType.CALCULATION,
                            evidence_ids=ev_ids,
                            materiality=MaterialityLevel.HIGH,
                            supporting_reasoning=f"Calculated via formula '{fm.formula}'"
                        )
                    )
                    if is_buyout:
                        if fm.metric_name == "EBITDA_Margin" and fm.value >= thresholds.get("min_ebitda_margin_pct", 0.15):
                            strengths.append(f"Strong unit EBITDA margin of {fm.value}%")
                        elif fm.metric_name == "Cash_Conversion" and fm.value >= 0.7:
                            strengths.append(f"High cash conversion of {fm.value}")
                        elif fm.metric_name == "Leverage_Ratio" and fm.value > thresholds.get("max_leverage_ratio", 4.0):
                            concerns.append(f"Excessive leverage ratio of {fm.value}x")
                    else:
                        if fm.metric_name == "LTV_CAC" and fm.value >= 3.0:
                            strengths.append(f"Strong LTV/CAC ratio of {fm.value}x")
                        elif fm.metric_name == "CAC_Payback" and fm.value <= thresholds.get("max_cac_payback_months", 18):
                            strengths.append(f"Fast CAC payback period of {fm.value} months")
                        elif fm.metric_name == "Gross_Margin" and fm.value >= (thresholds.get("min_gross_margin", 0.75) * 100 if thresholds.get("min_gross_margin", 0.75) <= 1.0 else thresholds.get("min_gross_margin", 0.75)):
                            strengths.append(f"High gross margin of {fm.value}% supporting SaaS economics")
                        elif fm.metric_name == "CAC_Payback" and fm.value > thresholds.get("max_cac_payback_months", 18):
                            concerns.append(f"Long CAC payback period of {fm.value} months")
                        elif fm.metric_name == "LTV_CAC" and fm.value < 2.0:
                            concerns.append(f"Sub-optimal LTV/CAC ratio of {fm.value}x")

            if not claims:
                fallback_ev_ids = valid_ev_ids[:1] if valid_ev_ids else []
                claims.append(
                    ClaimNode(
                        text=f"Unit economics metrics for {state.company_name} require additional detailed customer cohort data.",
                        claim_type=ClaimType.UNRESOLVED_QUESTION,
                        evidence_ids=fallback_ev_ids,
                        materiality=MaterialityLevel.MEDIUM,
                        supporting_reasoning="Granular unit economics metrics not fully detailed in initial materials."
                    )
                )
                concerns.append("Granular CAC and LTV breakdown required.")

            strat_label = "Traditional Buyout" if is_buyout else "Growth Equity SaaS"
            summary_str = f"Unit Economics Analysis for {state.company_name} ({strat_label} strategy). Evaluated CAC, LTV, payback, and gross margins across {len(claims)} claims."

            analysis = SpecialistAnalysis(
                domain=self.domain,
                summary=summary_str,
                claims=claims,
                strengths=strengths,
                concerns=concerns,
                confidence_score=0.85,
                iteration_count=iteration
            )

        analysis.domain = self.domain
        analysis.iteration_count = iteration
        state.specialist_analyses[self.domain] = analysis
        state.status = DiligenceStatus.SPECIALIST_DILIGENCE
        return state
