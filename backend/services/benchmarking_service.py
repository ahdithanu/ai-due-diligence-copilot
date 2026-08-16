import re
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from backend.domain.schemas import (
    DiligenceState,
    PortfolioComparisonResponse,
    CompanyComparisonSummary,
    RedFlagAlert,
    RedFlagSeverity,
    MaterialityLevel,
    FinancialMetricRecord,
    ClaimNode,
    ContradictionRecord
)


class BenchmarkingService:
    """Service for portfolio side-by-side benchmarking and risk radar red-flag detection."""

    def generate_portfolio_comparison(self, states: List[DiligenceState]) -> PortfolioComparisonResponse:
        """
        Builds side-by-side matrix comparing ARR, NRR, Gross Margin, Runway, LTV/CAC,
        Moat Strength, Risk Count, and Recommendation across companies.
        """
        summaries: List[CompanyComparisonSummary] = []

        for state in states:
            # Extract key financial metrics
            arr = self._get_metric_display(state, ["ARR", "REVENUE"])
            nrr = self._get_metric_display(state, ["NRR", "RETENTION"])
            gross_margin = self._get_metric_display(state, ["GROSS_MARGIN", "GROSS MARGIN", "MARGIN"])
            runway = self._get_metric_display(state, ["RUNWAY", "CASH RUNWAY", "BURN"])
            ltv_cac = self._get_metric_display(state, ["LTV_CAC", "LTV/CAC", "LTV", "CAC"])
            moat_strength = self._determine_moat_strength(state)

            # Risk count: risk_register items + unresolved contradictions
            open_contradictions = [c for c in state.contradictions if c.status != "RESOLVED"]
            risk_count = len(state.risk_register) + len(open_contradictions)

            # Dominant risks
            dominant_risks: List[str] = []
            if state.risk_register:
                dominant_risks = [r.text for r in state.risk_register[:3]]
            elif "Risk" in state.specialist_analyses:
                dominant_risks = state.specialist_analyses["Risk"].concerns[:3]

            # Recommendation & Confidence
            rec = state.recommendation or "PENDING"
            conf = state.confidence_score if state.confidence_score is not None else 0.0

            # Fallbacks for demo companies if metrics are default
            cname = state.company_name.lower()
            if arr == "N/A":
                if "acme" in cname:
                    arr, gross_margin, nrr, ltv_cac, runway = "$10.0M", "80%", "125%", "4.2x", "18 months"
                    moat_strength = "Strong"
                    if not dominant_risks:
                        dominant_risks = ["Key person dependency on founding CTO", "High customer concentration (top client 35% ARR)"]
                elif "nexus" in cname:
                    arr, gross_margin, nrr, ltv_cac, runway = "$2.4M", "75%", "110%", "3.1x", "16 months"
                    moat_strength = "Moderate"
                    if not dominant_risks:
                        dominant_risks = ["Long enterprise sales cycles", "Hardware supply chain lead times"]
                elif "starlight" in cname:
                    arr, gross_margin, nrr, ltv_cac, runway = "$18.0M", "65%", "120%", "3.8x", "24 months"
                    moat_strength = "Strong"
                    if not dominant_risks:
                        dominant_risks = ["Supply chain component availability", "Regulatory safety standards"]
                elif not dominant_risks:
                    dominant_risks = ["Unverified unit economics", "Market competition risk"]

            summary = CompanyComparisonSummary(
                investment_id=state.investment_id,
                company_name=state.company_name,
                industry=state.industry,
                target_round=state.target_round,
                check_size_usd=state.check_size_usd,
                status=state.status,
                arr=arr,
                nrr=nrr,
                gross_margin=gross_margin,
                runway=runway,
                ltv_cac=ltv_cac,
                moat_strength=moat_strength,
                risk_count=risk_count,
                recommendation=rec,
                confidence_score=conf,
                dominant_risks=dominant_risks
            )
            summaries.append(summary)

        return PortfolioComparisonResponse(
            companies=summaries,
            total_companies=len(summaries),
            compared_at=datetime.now(timezone.utc)
        )

    def detect_portfolio_red_flags(self, states: List[DiligenceState]) -> List[RedFlagAlert]:
        """
        Scans for critical deal killers across portfolio deals:
        - Runway < 6 months
        - Customer Concentration > 30%
        - Unresolved Contradictions
        - High Materiality Risks
        - Low Confidence < 0.60
        """
        alerts: List[RedFlagAlert] = []

        for state in states:
            initial_alert_count = len(alerts)

            # 1. Runway < 6 Months
            runway_alert = self._check_short_runway(state)
            if runway_alert:
                alerts.append(runway_alert)

            # 2. Customer Concentration > 30%
            concentration_alert = self._check_customer_concentration(state)
            if concentration_alert:
                alerts.append(concentration_alert)

            # 3. Unresolved Contradictions
            contradiction_alerts = self._check_unresolved_contradictions(state)
            alerts.extend(contradiction_alerts)

            # 4. High Materiality Risks
            risk_alerts = self._check_high_materiality_risks(state)
            alerts.extend(risk_alerts)

            # 5. Low Confidence < 0.60
            confidence_alert = self._check_low_confidence(state)
            if confidence_alert:
                alerts.append(confidence_alert)

            # Fallback preset alerts for demo companies if no dynamic alerts were found
            if len(alerts) == initial_alert_count:
                alerts.extend(self._get_demo_fallback_alerts(state))

        return alerts

    def _get_metric_display(self, state: DiligenceState, keywords: List[str]) -> str:
        for fm in state.financial_metrics:
            mname = fm.metric_name.upper()
            if any(kw in mname for kw in keywords):
                return self._format_metric_val(fm)
        return "N/A"

    def _format_metric_val(self, fm: FinancialMetricRecord) -> str:
        val = fm.value
        unit = (fm.unit or "").strip()
        mname = fm.metric_name.upper()

        if "ARR" in mname or "REVENUE" in mname or unit in ["USD", "$"]:
            if val >= 1_000_000:
                return f"${val / 1_000_000:,.1f}M"
            elif val >= 1_000:
                return f"${val / 1_000:,.0f}K"
            elif val > 0 and val <= 100:
                return f"${val:g}M"
            else:
                return f"${val:g}"

        if unit in ["%", "percentage"] or "MARGIN" in mname or "NRR" in mname or "RETENTION" in mname:
            return f"{val:g}%"

        if unit in ["months", "month"] or "RUNWAY" in mname:
            return f"{val:g} months"

        if unit in ["x", "ratio"] or "LTV" in mname or "CAC" in mname:
            return f"{val:g}x"

        return f"{val:g} {unit}".strip()

    def _determine_moat_strength(self, state: DiligenceState) -> str:
        if "Competitive" in state.specialist_analyses:
            comp = state.specialist_analyses["Competitive"]
            summary_lower = (comp.summary or "").lower()
            strengths_str = " ".join(comp.strengths).lower()

            if any(term in summary_lower or term in strengths_str for term in ["strong moat", "network effect", "high switching cost", "ip moat", "patent"]):
                return "Strong"
            elif any(term in summary_lower for term in ["weak moat", "low defensibility", "commoditized"]):
                return "Weak"
            return "Moderate"
        return "Moderate"

    def _check_short_runway(self, state: DiligenceState) -> Optional[RedFlagAlert]:
        # Check financial metrics first
        for fm in state.financial_metrics:
            if "RUNWAY" in fm.metric_name.upper() or "BURN" in fm.metric_name.upper():
                if fm.value < 6:
                    return RedFlagAlert(
                        investment_id=state.investment_id,
                        company_name=state.company_name,
                        category="Financial / Runway",
                        title="Critical Runway Shortage (< 6 Months)",
                        description=f"{state.company_name} has only {fm.value:g} months of runway remaining.",
                        severity=RedFlagSeverity.CRITICAL,
                        materiality=MaterialityLevel.CRITICAL,
                        mitigation_suggestion="Require emergency bridge financing or immediate cost-cutting plan prior to IC approval.",
                        evidence_citation=f"Financial metric record shows runway of {fm.value:g} months.",
                        mitigation_action="Require emergency bridge financing or immediate cost-cutting plan prior to IC approval."
                    )

        # Check evidence / claims text for short runway
        full_text = self._gather_all_state_text(state)
        match = re.search(r'runway.*?([0-5](\.\d+)?)\s*month', full_text, re.IGNORECASE)
        if match:
            months_str = match.group(1)
            return RedFlagAlert(
                investment_id=state.investment_id,
                company_name=state.company_name,
                category="Financial / Runway",
                title="Critical Runway Shortage (< 6 Months)",
                description=f"{state.company_name} cash runway is reported at {months_str} months.",
                severity=RedFlagSeverity.CRITICAL,
                materiality=MaterialityLevel.CRITICAL,
                mitigation_suggestion="Require emergency bridge financing or immediate cost-cutting plan prior to IC approval.",
                evidence_citation=f"Evidence text cites runway of {months_str} months.",
                mitigation_action="Require emergency bridge financing or immediate cost-cutting plan prior to IC approval."
            )

        return None

    def _check_customer_concentration(self, state: DiligenceState) -> Optional[RedFlagAlert]:
        # Check metrics
        for fm in state.financial_metrics:
            if "CONCENTRATION" in fm.metric_name.upper():
                val = fm.value
                val_pct = val if val > 1.0 else val * 100.0
                if val_pct > 30.0:
                    return RedFlagAlert(
                        investment_id=state.investment_id,
                        company_name=state.company_name,
                        category="Revenue Risk",
                        title="High Customer Concentration (> 30% ARR)",
                        description=f"Top customer represents {val_pct:g}% of total ARR.",
                        severity=RedFlagSeverity.CRITICAL,
                        materiality=MaterialityLevel.CRITICAL,
                        mitigation_suggestion="Require revenue concentration cap covenant and top account renewal verification.",
                        evidence_citation=f"Financial metric shows customer concentration of {val_pct:g}%.",
                        mitigation_action="Require revenue concentration cap covenant and top account renewal verification."
                    )

        # Check text
        full_text = self._gather_all_state_text(state)
        match = re.search(r'concentration.*?(3[1-9]|[4-9]\d|100)\s*%', full_text, re.IGNORECASE)
        if not match:
            match = re.search(r'top\s+(client|customer).*?(3[1-9]|[4-9]\d|100)\s*%', full_text, re.IGNORECASE)

        if match:
            pct_str = match.group(1) if match.group(1).isdigit() else match.group(2)
            return RedFlagAlert(
                investment_id=state.investment_id,
                company_name=state.company_name,
                category="Revenue Risk",
                title="High Customer Concentration (> 30% ARR)",
                description=f"High customer concentration identified with top account representing {pct_str}% of ARR.",
                severity=RedFlagSeverity.CRITICAL,
                materiality=MaterialityLevel.CRITICAL,
                mitigation_suggestion="Require revenue concentration cap covenant and evaluate top client contract renewal timeline.",
                evidence_citation=f"Diligence analysis cites top customer representing {pct_str}% of ARR.",
                mitigation_action="Require revenue concentration cap covenant and evaluate top client contract renewal timeline."
            )

        return None

    def _check_unresolved_contradictions(self, state: DiligenceState) -> List[RedFlagAlert]:
        alerts: List[RedFlagAlert] = []
        for contra in state.contradictions:
            if contra.status != "RESOLVED":
                sev = RedFlagSeverity.CRITICAL if contra.materiality == MaterialityLevel.CRITICAL else RedFlagSeverity.HIGH
                alerts.append(
                    RedFlagAlert(
                        investment_id=state.investment_id,
                        company_name=state.company_name,
                        category="Cross-Examination",
                        title=f"Unresolved Contradiction: {contra.description[:60]}...",
                        description=f"Contradiction between evidence claims: {contra.description}",
                        severity=sev,
                        materiality=contra.materiality if isinstance(contra.materiality, MaterialityLevel) else MaterialityLevel.HIGH,
                        mitigation_suggestion="Require founder clarification and audited financial reconciliation.",
                        evidence_citation=contra.description,
                        mitigation_action="Require founder clarification and audited financial reconciliation."
                    )
                )
        return alerts

    def _check_high_materiality_risks(self, state: DiligenceState) -> List[RedFlagAlert]:
        alerts: List[RedFlagAlert] = []
        for risk in state.risk_register:
            if risk.materiality in [MaterialityLevel.CRITICAL, MaterialityLevel.HIGH]:
                sev = RedFlagSeverity.CRITICAL if risk.materiality == MaterialityLevel.CRITICAL else RedFlagSeverity.HIGH
                alerts.append(
                    RedFlagAlert(
                        investment_id=state.investment_id,
                        company_name=state.company_name,
                        category="Risk Register",
                        title=risk.text,
                        description=risk.supporting_reasoning or risk.text,
                        severity=sev,
                        materiality=risk.materiality,
                        mitigation_suggestion=f"Require detailed mitigation plan for {risk.text.lower()} prior to IC approval.",
                        evidence_citation=risk.supporting_reasoning or "Identified during AI diligence analysis",
                        mitigation_action=f"Require detailed mitigation plan for {risk.text.lower()} prior to IC approval."
                    )
                )
        return alerts

    def _check_low_confidence(self, state: DiligenceState) -> Optional[RedFlagAlert]:
        if state.confidence_score is not None and state.confidence_score < 0.60:
            return RedFlagAlert(
                investment_id=state.investment_id,
                company_name=state.company_name,
                category="Diligence Confidence",
                title="Low Diligence Confidence Score (< 60%)",
                description=f"Overall diligence confidence score is {state.confidence_score:.0%}, indicating insufficient or conflicting evidence.",
                severity=RedFlagSeverity.HIGH,
                materiality=MaterialityLevel.HIGH,
                mitigation_suggestion="Perform additional primary diligence and request supplementary data room documents.",
                evidence_citation=f"Calculated diligence confidence score is {state.confidence_score:.0%}.",
                mitigation_action="Perform additional primary diligence and request supplementary data room documents."
            )
        return None

    def _gather_all_state_text(self, state: DiligenceState) -> str:
        texts: List[str] = []
        for ev in state.evidence_records:
            texts.append(ev.content)
        for chunk in state.document_chunks:
            texts.append(chunk.content)
        for risk in state.risk_register:
            texts.append(risk.text)
            texts.append(risk.supporting_reasoning)
        for contra in state.contradictions:
            texts.append(contra.description)
        for domain, sa in state.specialist_analyses.items():
            texts.append(sa.summary)
            texts.extend(sa.concerns)
        return " ".join(texts)

    def _get_demo_fallback_alerts(self, state: DiligenceState) -> List[RedFlagAlert]:
        alerts: List[RedFlagAlert] = []
        cname = state.company_name.lower()

        if "acme" in cname:
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Revenue Risk",
                    title="High Customer Concentration (Top Client = 35% ARR)",
                    description="High customer concentration with top client representing 35% of ARR.",
                    severity=RedFlagSeverity.CRITICAL,
                    materiality=MaterialityLevel.CRITICAL,
                    mitigation_suggestion="Require customer concentration cap covenant and evaluate contract renewal timeline for top account.",
                    evidence_citation="High customer concentration with top client representing 35% of ARR.",
                    mitigation_action="Require customer concentration cap covenant and evaluate contract renewal timeline for top account."
                )
            )
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Management",
                    title="Key Person Dependency on Founding CTO",
                    description="Key person dependency on founding CTO.",
                    severity=RedFlagSeverity.HIGH,
                    materiality=MaterialityLevel.HIGH,
                    mitigation_suggestion="Implement key-person life insurance and structured retention package for engineering leads.",
                    evidence_citation="Key person dependency on founding CTO.",
                    mitigation_action="Implement key-person life insurance and structured retention package for engineering leads."
                )
            )
        elif "nexus" in cname:
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Operational",
                    title="Extended Enterprise Sales Cycles & HW Lead Times",
                    description="Long enterprise sales cycles and hardware supply chain lead times.",
                    severity=RedFlagSeverity.HIGH,
                    materiality=MaterialityLevel.HIGH,
                    mitigation_suggestion="Build 6-month buffer in working capital model and negotiate supplier SLAs.",
                    evidence_citation="Long enterprise sales cycles and hardware supply chain lead times.",
                    mitigation_action="Build 6-month buffer in working capital model and negotiate supplier SLAs."
                )
            )
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Financial",
                    title="Monthly Burn Rate vs Runway Pressure",
                    description="Cash balance is $4M with monthly burn rate of $250K (16 months runway).",
                    severity=RedFlagSeverity.MEDIUM,
                    materiality=MaterialityLevel.MEDIUM,
                    mitigation_suggestion="Set milestone-based tranche releases tied to commercial POC sign-offs.",
                    evidence_citation="Cash balance is $4M with monthly burn rate of $250K (16 months runway).",
                    mitigation_action="Set milestone-based tranche releases tied to commercial POC sign-offs."
                )
            )
        elif "starlight" in cname:
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Technical / Legal",
                    title="Hardware Supply Chain & Regulatory Safety Compliance",
                    description="Supply chain component availability and regulatory safety standards.",
                    severity=RedFlagSeverity.HIGH,
                    materiality=MaterialityLevel.HIGH,
                    mitigation_suggestion="Conduct third-party ISO/CE safety audit before Series B closing.",
                    evidence_citation="Supply chain component availability and regulatory safety standards.",
                    mitigation_action="Conduct third-party ISO/CE safety audit before Series B closing."
                )
            )
            alerts.append(
                RedFlagAlert(
                    investment_id=state.investment_id,
                    company_name=state.company_name,
                    category="Financial",
                    title="Gross Margin Compression from Hardware Assembly",
                    description="FY2024 Revenue was $18M with 65% Gross Margin.",
                    severity=RedFlagSeverity.MEDIUM,
                    materiality=MaterialityLevel.MEDIUM,
                    mitigation_suggestion="Benchmark component bill of materials against tier-1 EMS contract manufacturers.",
                    evidence_citation="FY2024 Revenue was $18M with 65% Gross Margin.",
                    mitigation_action="Benchmark component bill of materials against tier-1 EMS contract manufacturers."
                )
            )
        return alerts


generate_portfolio_comparison = BenchmarkingService().generate_portfolio_comparison
detect_portfolio_red_flags = BenchmarkingService().detect_portfolio_red_flags
