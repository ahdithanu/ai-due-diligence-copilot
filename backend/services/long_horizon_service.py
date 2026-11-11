import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from backend.domain.schemas import (
    SignalType,
    SignalSource,
    SignalEvent,
    AgentSubscription,
    DurableConstraint,
    PartnerActionItem,
    FirmStrategicMandate,
    LongHorizonSpaceResponse,
    IngestSignalRequest,
    ResolveActionRequest,
    CreateConstraintRequest,
    CreateMandateRequest,
)

DEFAULT_SUBSCRIPTIONS = [
    {
        "agent_name": "Cap Table & Dilution Sentry Agent",
        "interested_signal_types": [
            SignalType.DATA_ROOM_FILE_DROPPED,
            SignalType.FOUNDER_EMAIL_RECEIVED,
        ],
        "wake_condition": "File touches 'Cap Table' OR contains equity/dilution keywords",
        "schedule_interval_sec": 3600,
    },
    {
        "agent_name": "QoE & Working Capital Sentinel Agent",
        "interested_signal_types": [
            SignalType.DATA_ROOM_FILE_DROPPED,
            SignalType.CUSTODIAN_SETTLEMENT_EVENT,
        ],
        "wake_condition": "Financial statement or revenue ledger upload",
        "schedule_interval_sec": 7200,
    },
    {
        "agent_name": "Customer Retention & Churn Watcher",
        "interested_signal_types": [
            SignalType.DATA_ROOM_FILE_DROPPED,
            SignalType.MARKET_BENCHMARK_SHIFT,
        ],
        "wake_condition": "Customer cohort updates or competitor win/loss shifts",
        "schedule_interval_sec": 86400,
    },
    {
        "agent_name": "Governance & Anti-Dilution Covenants Agent",
        "interested_signal_types": [
            SignalType.TASK_COMPLETED_BY_HUMAN,
            SignalType.MANDATE_PROPAGATED,
        ],
        "wake_condition": "Partner approves term sheet or firm policy changes",
        "schedule_interval_sec": 14400,
    },
]

DEFAULT_CONSTRAINTS = [
    {
        "category": "EQUITY_STRUCTURE",
        "rule_text": "Never permit founder common voting equity to compress below 51% in primary round modeling.",
        "source": "Elena (CEO) verbal commitment during partner dinner on 2026-09-15",
    },
    {
        "category": "VENDOR_RESTRICTION",
        "rule_text": "Do not recommend displacing AWS infrastructure with Azure; target holds $450k non-transferable AWS EDP credits.",
        "source": "Technical Director interview note from Day 4",
    },
    {
        "category": "KEY_PERSON_TERMS",
        "rule_text": "Founding CTO holds cryptographic master key escrow; any covenant must require VP Eng dual-custody prior to Series B.",
        "source": "Security Architecture audit note on Day 8",
    },
]

DEFAULT_MANDATES = [
    {
        "mandate_name": "Firm-Wide Proactive QSBS Section 1202 & Tax Shield Audit",
        "description": "Every deal evaluated in Q1 must be proactively audited for federal QSBS eligibility and state nexus liabilities prior to partner review.",
        "target_frequency": "EVERY_DATA_ROOM_DROP",
        "enforcement_level": "MANDATORY_ALL_DEALS",
        "active": True,
        "deals_enforced_count": 4,
    },
    {
        "mandate_name": "Automated 40% AI Inference Margin Stress Test",
        "description": "Any company utilizing commercial LLM APIs must be automatically modeled with a 40% margin compression stress case.",
        "target_frequency": "ON_EVALUATION",
        "enforcement_level": "MANDATORY_ALL_DEALS",
        "active": True,
        "deals_enforced_count": 6,
    },
]

DEFAULT_SIGNALS = [
    {
        "signal_type": SignalType.DATA_ROOM_FILE_DROPPED,
        "source": SignalSource.EXTERNAL_WORLD,
        "title": "Data Room Signal: Founder uploaded 'Acme_Series_A_CapTable_v3_Final.xlsx'",
        "payload": {"filename": "Acme_Series_A_CapTable_v3_Final.xlsx", "size_kb": 840, "folder": "01_Corporate_Governance"},
        "acting_agents": ["Cap Table & Dilution Sentry Agent"],
    },
    {
        "signal_type": SignalType.FOUNDER_EMAIL_RECEIVED,
        "source": SignalSource.EXTERNAL_WORLD,
        "title": "Email Signal from Elena (CEO): 'Clarifying Anchor Customer Q3 Renewal Terms'",
        "payload": {"sender": "elena@acmeai.io", "subject": "Clarifying Anchor Customer Q3 Renewal Terms", "has_attachment": False},
        "acting_agents": ["Customer Retention & Churn Watcher", "Governance & Anti-Dilution Covenants Agent"],
    },
    {
        "signal_type": SignalType.SCHEDULED_TIMER_WAKE,
        "source": SignalSource.AGENT_SCHEDULE,
        "title": "Autonomous Timer: 72-hour silent window elapsed for patent assignment delivery",
        "payload": {"scheduled_agent": "Governance & Anti-Dilution Covenants Agent", "target": "Founding CTO IP Assignment"},
        "acting_agents": ["Governance & Anti-Dilution Covenants Agent"],
    },
]

DEFAULT_ACTIONS = [
    {
        "agent_proposer": "Cap Table & Dilution Sentry Agent",
        "priority": "CRITICAL",
        "headline": "Cap Table Update Detected: Unallocated ESOP diluted from 15% to 11.5% with founder grant",
        "background_work_summary": "Agent parsed uploaded spreadsheet, recalculated the $25M-$500M liquidation waterfall, and reconciled against durable constraint #1 (Founder voting control). Series A effective post-money valuation compressed by $1.75M. Draft clarification email to lead legal counsel prepared.",
        "precomputed_impact": {"dilution_shift": "+3.5%", "series_a_moic_delta": "-0.18x", "esop_pool_status": "DEFICIT"},
        "action_type": "DISPATCH_CLARIFICATION",
        "one_click_action_label": "1-Click Approve & Send Inquiry to Target Counsel",
        "proposed_payload": {
            "recipient": "legal@acmeai.io",
            "subject": "Inquiry regarding ESOP Pool expansion vs Common Stock grant in CapTable v3",
            "suggested_covenant": "Re-expand ESOP to 15.0% pre-money before execution of definitive agreements",
        },
    },
    {
        "agent_proposer": "QoE & Working Capital Sentinel Agent",
        "priority": "HIGH",
        "headline": "Q3 Revenue Discrepancy: $650k professional services fee booked as recurring ARR",
        "background_work_summary": "Agent reconciled stripe ledger against pitch deck statement. True recurring ARR is $9.35M (vs $10.0M reported). Agent recalculated the peer comps multiple: at 12.0x blended ARR, proposed entry valuation drops from $50.0M to $46.75M. Prepared valuation adjustment counter-proposal.",
        "precomputed_impact": {"arr_adjustment_usd": -650000, "implied_valuation_delta_usd": -3250000},
        "action_type": "PROPOSE_VALUATION_ADJUSTMENT",
        "one_click_action_label": "1-Click Adopt $46.75M Counter-Valuation",
        "proposed_payload": {
            "revised_arr": 9350000,
            "counter_valuation": 46750000,
            "memo_section_updated": "Section 4: Financial Quality of Earnings (QoE)",
        },
    },
    {
        "agent_proposer": "Governance & Anti-Dilution Covenants Agent",
        "priority": "ROUTINE",
        "headline": "Firm Mandate Enforced: Proactive QSBS Section 1202 Tax Exemption Verified",
        "background_work_summary": "Agent audited Delaware C-Corp founding docs against IRS Section 1202 criteria: gross assets under $50M at issuance, active qualified trade. 100% of Series A preferred shares qualify for federal capital gains exclusion (potential $10M tax shield per LP). Audit certificate drafted.",
        "precomputed_impact": {"lp_tax_shield_usd": 10000000, "qsbs_qualified": True},
        "action_type": "CONFIRM_TAX_SHIELD",
        "one_click_action_label": "1-Click Certify QSBS Qualification in IC Memo",
        "proposed_payload": {"certificate_ref": "QSBS-SEC-1202-CERT-2026", "audit_complete": True},
    },
]


class LongHorizonService:
    """
    Arca-style Long-Horizon Autonomous Engine:
    - Background agents watch the world so humans don't have to (Signals & Watchers).
    - Agents prompt humans with 1-click approvals after doing 90% of the work.
    - Durable memory holds entity constraints over 30-60 day deal horizons.
    - Firm leadership steers the firm by steering agent goals.
    """

    def __init__(self):
        self._signals: Dict[str, List[SignalEvent]] = {}
        self._subscriptions: Dict[str, List[AgentSubscription]] = {}
        self._constraints: Dict[str, List[DurableConstraint]] = {}
        self._actions: Dict[str, List[PartnerActionItem]] = {}
        self._mandates: List[FirmStrategicMandate] = [
            FirmStrategicMandate(
                id=str(uuid.uuid4()),
                mandate_name=m["mandate_name"],
                description=m["description"],
                target_frequency=m["target_frequency"],
                enforcement_level=m["enforcement_level"],
                active=m["active"],
                deals_enforced_count=m["deals_enforced_count"],
            )
            for m in DEFAULT_MANDATES
        ]

    def _init_deal_space(self, inv_id: str):
        now_str = datetime.now(timezone.utc).isoformat()
        if inv_id not in self._subscriptions:
            self._subscriptions[inv_id] = [
                AgentSubscription(
                    id=str(uuid.uuid4()),
                    agent_name=s["agent_name"],
                    investment_id=inv_id,
                    interested_signal_types=s["interested_signal_types"],
                    wake_condition=s["wake_condition"],
                    schedule_interval_sec=s["schedule_interval_sec"],
                    last_woken_at=now_str,
                )
                for s in DEFAULT_SUBSCRIPTIONS
            ]

        if inv_id not in self._constraints:
            self._constraints[inv_id] = [
                DurableConstraint(
                    id=str(uuid.uuid4()),
                    investment_id=inv_id,
                    category=c["category"],
                    rule_text=c["rule_text"],
                    source=c["source"],
                    is_active=True,
                    created_at=now_str,
                )
                for c in DEFAULT_CONSTRAINTS
            ]

        if inv_id not in self._signals:
            self._signals[inv_id] = [
                SignalEvent(
                    id=str(uuid.uuid4()),
                    investment_id=inv_id,
                    signal_type=sig["signal_type"],
                    source=sig["source"],
                    title=sig["title"],
                    payload=sig["payload"],
                    created_at=now_str,
                    processed=True,
                    acting_agents=sig["acting_agents"],
                )
                for sig in DEFAULT_SIGNALS
            ]

        if inv_id not in self._actions:
            self._actions[inv_id] = [
                PartnerActionItem(
                    id=str(uuid.uuid4()),
                    investment_id=inv_id,
                    agent_proposer=act["agent_proposer"],
                    priority=act["priority"],
                    status="PENDING_APPROVAL",
                    headline=act["headline"],
                    background_work_summary=act["background_work_summary"],
                    precomputed_impact=act["precomputed_impact"],
                    action_type=act["action_type"],
                    one_click_action_label=act["one_click_action_label"],
                    proposed_payload=act["proposed_payload"],
                    created_at=now_str,
                )
                for act in DEFAULT_ACTIONS
            ]

    def get_space(self, investment_id: str, company_name: str = "Acme SaaS AI") -> LongHorizonSpaceResponse:
        self._init_deal_space(investment_id)
        actions = self._actions[investment_id]
        signals = self._signals[investment_id]
        constraints = self._constraints[investment_id]
        subs = self._subscriptions[investment_id]

        pending_actions = [a for a in actions if a.status == "PENDING_APPROVAL"]

        return LongHorizonSpaceResponse(
            investment_id=investment_id,
            company_name=company_name,
            active_agents_count=len(subs),
            signals_processed_count=len(signals),
            pending_actions_count=len(pending_actions),
            pending_actions=actions,
            recent_signals=signals,
            durable_constraints=constraints,
            active_mandates=self._mandates,
            subscriptions=subs,
        )

    def ingest_signal(self, investment_id: str, req: IngestSignalRequest) -> SignalEvent:
        self._init_deal_space(investment_id)
        now_str = datetime.now(timezone.utc).isoformat()

        # Find agents who registered interest in this signal type
        acting_agents: List[str] = []
        for sub in self._subscriptions[investment_id]:
            if req.signal_type in sub.interested_signal_types:
                acting_agents.append(sub.agent_name)
                sub.last_woken_at = now_str

        sig = SignalEvent(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            signal_type=req.signal_type,
            source=req.source,
            title=req.title,
            payload=req.payload,
            created_at=now_str,
            processed=True,
            acting_agents=acting_agents if acting_agents else ["Autonomous Event Dispatcher"],
        )
        self._signals[investment_id].insert(0, sig)

        # Autonomous Work Trigger:
        # If an external signal arrives, agents proactively prepare a new PartnerActionItem
        if req.source == SignalSource.EXTERNAL_WORLD:
            new_action = PartnerActionItem(
                id=str(uuid.uuid4()),
                investment_id=investment_id,
                agent_proposer=acting_agents[0] if acting_agents else "Autonomous Lead Agent",
                priority="HIGH",
                status="PENDING_APPROVAL",
                headline=f"Autonomous Analysis: Reaction to {req.title}",
                background_work_summary=f"Agent evaluated incoming signal payload against 30-day deal memory. Validated financial and legal impact across model. 90% of synthesis complete.",
                precomputed_impact={"signal_correlated": True, "analysis_latency_ms": 420},
                action_type="REVIEW_SIGNAL_IMPACT",
                one_click_action_label="1-Click Confirm & Integrate into Active Diligence Memo",
                proposed_payload=req.payload,
                created_at=now_str,
            )
            self._actions[investment_id].insert(0, new_action)

        return sig

    def resolve_action(
        self, investment_id: str, action_id: str, req: ResolveActionRequest
    ) -> Optional[PartnerActionItem]:
        self._init_deal_space(investment_id)
        actions = self._actions[investment_id]
        for act in actions:
            if act.id == action_id:
                act.status = "APPROVED" if req.approved else "REJECTED"
                act.resolution_notes = req.resolution_notes or (
                    "Approved via 1-Click Executive Decision" if req.approved else "Rejected by Deal Partner"
                )

                # Arca Chapter 8: Human resolving an action is itself a signal that wakes other downstream agents!
                now_str = datetime.now(timezone.utc).isoformat()
                feedback_signal = SignalEvent(
                    id=str(uuid.uuid4()),
                    investment_id=investment_id,
                    signal_type=SignalType.TASK_COMPLETED_BY_HUMAN,
                    source=SignalSource.INTERNAL_UI,
                    title=f"Internal Action Resolved: {act.headline} ({act.status})",
                    payload={"action_id": action_id, "approved": req.approved, "notes": act.resolution_notes},
                    created_at=now_str,
                    processed=True,
                    acting_agents=["Governance & Anti-Dilution Covenants Agent"],
                )
                self._signals[investment_id].insert(0, feedback_signal)
                return act
        return None

    def add_constraint(self, investment_id: str, req: CreateConstraintRequest) -> DurableConstraint:
        self._init_deal_space(investment_id)
        now_str = datetime.now(timezone.utc).isoformat()
        c = DurableConstraint(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            category=req.category,
            rule_text=req.rule_text,
            source=req.source,
            is_active=True,
            created_at=now_str,
        )
        self._constraints[investment_id].append(c)
        return c

    def add_mandate(self, req: CreateMandateRequest) -> FirmStrategicMandate:
        m = FirmStrategicMandate(
            id=str(uuid.uuid4()),
            mandate_name=req.mandate_name,
            description=req.description,
            target_frequency=req.target_frequency,
            enforcement_level=req.enforcement_level,
            active=True,
            deals_enforced_count=1,
        )
        self._mandates.append(m)
        return m


long_horizon_service = LongHorizonService()
