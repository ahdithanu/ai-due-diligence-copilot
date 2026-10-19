import uuid
from typing import Dict, List, Optional
from backend.domain.schemas import (
    ConditionPrecedent,
    ConditionPrecedentStatus,
    EscrowHoldback,
    GovernanceCovenant,
    ValueCreationMilestone,
    RemediationPlanResponse,
    CreateMilestoneRequest,
)

DEFAULT_CONDITIONS = [
    {
        "category": "LEGAL",
        "condition_text": "Founding CTO executes comprehensive IP Assignment and delivers GitHub & AWS master signing keys.",
        "status": ConditionPrecedentStatus.SATISFIED,
        "responsible_party": "Founding CTO",
        "target_deadline": "Prior to Signing",
        "risk_mitigated": "Key Person & Intellectual Property Ownership Risk",
    },
    {
        "category": "COMMERCIAL",
        "condition_text": "Top enterprise customer (representing 35% of ARR) executes 24-month contract renewal without termination for convenience.",
        "status": ConditionPrecedentStatus.PENDING_TARGET_ACTION,
        "responsible_party": "CEO & Lead Counsel",
        "target_deadline": "Closing Condition Precedent (CP)",
        "risk_mitigated": "Extreme Customer Concentration & Churn Volatility",
    },
    {
        "category": "INSURANCE",
        "condition_text": "Target binds $10.0M Directors & Officers (D&O) insurance tail policy with A-rated carrier.",
        "status": ConditionPrecedentStatus.SATISFIED,
        "responsible_party": "Target Finance Lead",
        "target_deadline": "Closing Condition Precedent (CP)",
        "risk_mitigated": "Pre-closing Officer Liability & Breach of Fiduciary Duty",
    },
    {
        "category": "MANAGEMENT",
        "condition_text": "Co-founders execute fresh 4-year reverse dilution vesting agreements with 1-year cliff on 25% equity holdings.",
        "status": ConditionPrecedentStatus.PENDING_TARGET_ACTION,
        "responsible_party": "Founders",
        "target_deadline": "Simultaneous with Closing",
        "risk_mitigated": "Early Founder Departure & Equity Dilution Overhang",
    },
    {
        "category": "TECH",
        "condition_text": "Remediate 2 open-source AGPL-licensed microservices identified during automated SBOM audit.",
        "status": ConditionPrecedentStatus.SATISFIED,
        "responsible_party": "VP Engineering",
        "target_deadline": "Prior to Closing",
        "risk_mitigated": "Viral Copyleft Licensing Liability",
    },
]

DEFAULT_ESCROWS = [
    {
        "title": "Special Customer Concentration Indemnity Escrow",
        "holdback_amount_usd": 3_000_000.0,
        "holdback_pct": 6.0,
        "survival_period_months": 18,
        "trigger_event": "Termination or contract reduction > 25% by Anchor Customer within 18 months of closing.",
        "release_conditions": "50% released at 12 months if contract active; remainder released at 18 months.",
    },
    {
        "title": "General Fundamental Representations & Tax Escrow",
        "holdback_amount_usd": 2_000_000.0,
        "holdback_pct": 4.0,
        "survival_period_months": 12,
        "trigger_event": "Undisclosed state sales tax nexus liability or capitalized lease claim.",
        "release_conditions": "100% released at 12-month anniversary subject to unresolved claim holds.",
    },
]

DEFAULT_COVENANTS = [
    {
        "covenant_type": "BOARD_GOVERNANCE",
        "clause_title": "Board of Directors Reconstitution",
        "description": "5-member Board: 2 Sponsor Designees, 2 Founder Designees, and 1 Independent Industry Operator mutually approved.",
        "threshold_usd": None,
    },
    {
        "covenant_type": "NEGATIVE",
        "clause_title": "Debt & Indebtedness Incurrence Restriction",
        "description": "Target shall not incur, assume, or guarantee any indebtedness in excess of $1,000,000 without prior written Sponsor consent.",
        "threshold_usd": 1_000_000.0,
    },
    {
        "covenant_type": "NEGATIVE",
        "clause_title": "Material M&A & Liquidation Hurdle Veto",
        "description": "Sale, merger, or asset liquidation generating less than 3.0x return on invested capital requires Preferred Class approval.",
        "threshold_usd": None,
    },
    {
        "covenant_type": "AFFIRMATIVE",
        "clause_title": "Senior Executive Compensation Committee Governance",
        "description": "All executive officer salaries, bonuses, and equity grants exceeding $350,000/year subject to Compensation Committee oversight.",
        "threshold_usd": 350_000.0,
    },
]

DEFAULT_MILESTONES = [
    # Days 1 - 30
    {
        "day_range": "DAYS_1_30",
        "workstream": "FINANCE_OPS",
        "milestone_title": "Migrate QuickBooks to NetSuite & Establish ASC 606 Revenue Recognition",
        "target_kpi_impact": "Accelerate monthly close from 25 days to 6 days; eliminate manual revenue audit adjustments.",
        "owner": "Finance Operating Partner",
        "status": "IN_PROGRESS",
    },
    {
        "day_range": "DAYS_1_30",
        "workstream": "TECH_ARCH",
        "milestone_title": "Mandatory Hardware MFA on Cloud Control Plane & Secret Key Rotation",
        "target_kpi_impact": "Achieve SOC 2 Type II baseline compliance; eliminate root account access risk.",
        "owner": "Cyber Operating Partner",
        "status": "ACHIEVED",
    },
    # Days 31 - 60
    {
        "day_range": "DAYS_31_60",
        "workstream": "GTM_EXPANSION",
        "milestone_title": "Hire Enterprise VP of Sales & Roll Out Value-Based Pricing Tiers",
        "target_kpi_impact": "Expand quota capacity by $6.0M ARR; improve average contract value (ACV) from $45k to $75k.",
        "owner": "GTM Operating Partner",
        "status": "PLANNED",
    },
    {
        "day_range": "DAYS_31_60",
        "workstream": "FINANCE_OPS",
        "milestone_title": "Renegotiate Cloud Vendor Master Services Agreement (AWS EDP)",
        "target_kpi_impact": "Achieve 28% compute cost reduction; improve gross margin from 80% to 83.5%.",
        "owner": "Procurement Lead",
        "status": "PLANNED",
    },
    # Days 61 - 100
    {
        "day_range": "DAYS_61_100",
        "workstream": "TECH_ARCH",
        "milestone_title": "Launch Automated Customer Health Telemetry & AI Churn Early-Warning System",
        "target_kpi_impact": "Suppress annual gross revenue churn below 3.0%; lift NRR from 125% to 132%.",
        "owner": "Product Lead",
        "status": "PLANNED",
    },
    {
        "day_range": "DAYS_61_100",
        "workstream": "TALENT_HR",
        "milestone_title": "Recruit Independent Board Member & Finalize 2027 Long-Term Incentive Plan",
        "target_kpi_impact": "Ensure executive retention and align key management with $250M exit milestone.",
        "owner": "Deal Lead",
        "status": "PLANNED",
    },
]


class RemediationCovenantsService:
    """Manages pre-closing conditions precedent, indemnity escrows, covenants, and 100-day value creation roadmaps."""

    def __init__(self):
        self._conditions: Dict[str, List[ConditionPrecedent]] = {}
        self._milestones: Dict[str, List[ValueCreationMilestone]] = {}

    def _get_conditions(self, inv_id: str) -> List[ConditionPrecedent]:
        if inv_id not in self._conditions:
            self._conditions[inv_id] = [
                ConditionPrecedent(
                    id=str(uuid.uuid4()),
                    category=c["category"],
                    condition_text=c["condition_text"],
                    status=c["status"],
                    responsible_party=c["responsible_party"],
                    target_deadline=c["target_deadline"],
                    risk_mitigated=c["risk_mitigated"],
                )
                for c in DEFAULT_CONDITIONS
            ]
        return self._conditions[inv_id]

    def _get_milestones(self, inv_id: str) -> List[ValueCreationMilestone]:
        if inv_id not in self._milestones:
            self._milestones[inv_id] = [
                ValueCreationMilestone(
                    id=str(uuid.uuid4()),
                    day_range=m["day_range"],
                    workstream=m["workstream"],
                    milestone_title=m["milestone_title"],
                    target_kpi_impact=m["target_kpi_impact"],
                    owner=m["owner"],
                    status=m["status"],
                )
                for m in DEFAULT_MILESTONES
            ]
        return self._milestones[inv_id]

    def get_remediation_plan(
        self,
        investment_id: str,
        company_name: str = "Acme SaaS AI",
        valuation_usd: float = 50_000_000.0,
    ) -> RemediationPlanResponse:
        conditions = self._get_conditions(investment_id)
        milestones = self._get_milestones(investment_id)

        escrows = [
            EscrowHoldback(
                id=str(uuid.uuid4()),
                title=e["title"],
                holdback_amount_usd=e["holdback_amount_usd"],
                holdback_pct=e["holdback_pct"],
                survival_period_months=e["survival_period_months"],
                trigger_event=e["trigger_event"],
                release_conditions=e["release_conditions"],
            )
            for e in DEFAULT_ESCROWS
        ]

        total_escrow = sum(e.holdback_amount_usd for e in escrows)

        covenants = [
            GovernanceCovenant(
                id=str(uuid.uuid4()),
                covenant_type=c["covenant_type"],
                clause_title=c["clause_title"],
                description=c["description"],
                threshold_usd=c["threshold_usd"],
            )
            for c in DEFAULT_COVENANTS
        ]

        return RemediationPlanResponse(
            investment_id=investment_id,
            company_name=company_name,
            total_escrow_holdback_usd=total_escrow,
            conditions_precedent=conditions,
            escrows=escrows,
            covenants=covenants,
            value_creation_plan=milestones,
        )

    def update_condition_status(
        self, investment_id: str, cp_id: str, status: ConditionPrecedentStatus
    ) -> Optional[ConditionPrecedent]:
        conditions = self._get_conditions(investment_id)
        for cp in conditions:
            if cp.id == cp_id:
                cp.status = status
                return cp
        return None

    def add_milestone(
        self, investment_id: str, req: CreateMilestoneRequest
    ) -> ValueCreationMilestone:
        milestones = self._get_milestones(investment_id)
        new_m = ValueCreationMilestone(
            id=str(uuid.uuid4()),
            day_range=req.day_range,
            workstream=req.workstream,
            milestone_title=req.milestone_title,
            target_kpi_impact=req.target_kpi_impact,
            owner=req.owner,
            status="PLANNED",
        )
        milestones.append(new_m)
        return new_m


remediation_covenants_service = RemediationCovenantsService()
