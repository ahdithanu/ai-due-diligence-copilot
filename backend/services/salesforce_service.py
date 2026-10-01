import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.domain.schemas import (
    SalesforceOpportunity,
    AgentforceActionRequest,
    AgentforceActionResponse,
    SalesforceDataCloudSyncResult
)


class SalesforceService:
    """
    Enterprise Salesforce Agentforce & Data Cloud Zero-Copy Integration Service.
    
    Provides:
    1. Agentforce Invocable Action Executor: Invokes agent actions from Salesforce Flow & Agentforce.
    2. Data Cloud Zero-Copy Ingestion: Federated lakehouse query mapping without data duplication.
    3. Bi-directional CRM Sync: Updates Opportunity stages, diligence scores, and posts to Chatter.
    """

    def __init__(self):
        # In-memory mock Salesforce CRM Opportunities: opp_id -> SalesforceOpportunity
        self._opportunities: Dict[str, SalesforceOpportunity] = {
            "006Dn000003ABC1": SalesforceOpportunity(
                opp_id="006Dn000003ABC1",
                account_name="Apex Cyber Solutions",
                stage_name="Proposal / Due Diligence",
                amount_usd=10_000_000.0,
                close_date="2026-11-15",
                lead_partner="Sarah Jenkins",
                investment_id="inv-apex-cyber-001",
                diligence_score=87.5,
                data_room_url="https://dataroom.apexcyber.io/v/sharepoint-apex"
            ),
            "006Dn000003XYZ2": SalesforceOpportunity(
                opp_id="006Dn000003XYZ2",
                account_name="Horizon Logistics AI",
                stage_name="Initial Screening",
                amount_usd=15_000_000.0,
                close_date="2026-12-01",
                lead_partner="Marcus Vance",
                investment_id="inv-horizon-logistics-002",
                diligence_score=None,
                data_room_url="https://box.com/s/horizon-logistics-room"
            )
        }
        # In-memory chatter feed posts: opp_id -> List[Dict]
        self._chatter_feed: Dict[str, List[Dict[str, Any]]] = {}

    def get_opportunity(self, opp_id: str) -> Optional[SalesforceOpportunity]:
        return self._opportunities.get(opp_id)

    def list_opportunities(self) -> List[SalesforceOpportunity]:
        return list(self._opportunities.values())

    def get_agentforce_actions_metadata(self) -> List[Dict[str, Any]]:
        """
        Returns OpenAPI-compatible Agentforce Invocable Action definitions.
        Salesforce admins import this into Agentforce / External Services.
        """
        return [
            {
                "name": "RunDiligenceAudit",
                "label": "Run AI Due Diligence Audit",
                "description": "Triggers multi-agent institutional analysis on target company documents and financial models.",
                "inputs": [
                    {"name": "opportunity_id", "type": "String", "required": True, "description": "Salesforce 18-character Opportunity ID"}
                ],
                "outputs": [
                    {"name": "status", "type": "String"},
                    {"name": "composite_score", "type": "Number"},
                    {"name": "contradictions_found", "type": "Integer"}
                ]
            },
            {
                "name": "GetInvestmentScorecard",
                "label": "Get Investment Scorecard",
                "description": "Retrieves audited financial metrics (ARR, NRR, EBITDA, Runway) for Salesforce Opportunity.",
                "inputs": [
                    {"name": "opportunity_id", "type": "String", "required": True}
                ],
                "outputs": [
                    {"name": "arr_usd", "type": "Number"},
                    {"name": "nrr_pct", "type": "Number"},
                    {"name": "runway_months", "type": "Number"},
                    {"name": "recommendation", "type": "String"}
                ]
            },
            {
                "name": "PostChatterMemoSummary",
                "label": "Post IC Memo Summary to Chatter",
                "description": "Publishes Bull vs Bear synthesized investment memo directly to Opportunity Chatter feed.",
                "inputs": [
                    {"name": "opportunity_id", "type": "String", "required": True},
                    {"name": "memo_headline", "type": "String", "required": False}
                ],
                "outputs": [
                    {"name": "chatter_post_id", "type": "String"},
                    {"name": "published_at", "type": "String"}
                ]
            }
        ]

    def execute_agentforce_action(self, request: AgentforceActionRequest) -> AgentforceActionResponse:
        """
        Executes an Agentforce Invocable Action invoked by Salesforce Agentforce or Flow.
        """
        start = time.perf_counter()
        opp = self.get_opportunity(request.opportunity_id)
        if not opp:
            return AgentforceActionResponse(
                success=False,
                action_name=request.action_name,
                output_parameters={"error": f"Opportunity '{request.opportunity_id}' not found."},
                chatter_post_created=False,
                execution_time_ms=0.0
            )

        if request.action_name == "RunDiligenceAudit":
            opp.stage_name = "Due Diligence Review"
            opp.diligence_score = 88.0
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            return AgentforceActionResponse(
                success=True,
                action_name=request.action_name,
                output_parameters={
                    "status": "COMPLETED",
                    "opportunity_id": opp.opp_id,
                    "account_name": opp.account_name,
                    "composite_score": 88.0,
                    "contradictions_found": 1,
                    "contradiction_summary": "ARR mismatch between Deck ($12M) vs CRM/GL ($8M) flagged for review."
                },
                chatter_post_created=False,
                execution_time_ms=elapsed
            )

        elif request.action_name == "GetInvestmentScorecard":
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            return AgentforceActionResponse(
                success=True,
                action_name=request.action_name,
                output_parameters={
                    "opportunity_id": opp.opp_id,
                    "account_name": opp.account_name,
                    "arr_usd": 12_500_000.0,
                    "nrr_pct": 128.0,
                    "runway_months": 18.0,
                    "gross_margin_pct": 78.5,
                    "recommendation": "PROCEED_TO_IC_DEBATE"
                },
                chatter_post_created=False,
                execution_time_ms=elapsed
            )

        elif request.action_name == "PostChatterMemoSummary":
            post_id = f"0D5Dn0000{uuid.uuid4().hex[:7]}"
            post_body = (
                f"🤖 [AI Due Diligence Copilot] IC Synthesis for {opp.account_name}:\n"
                f"• Investment Recommendation: PROCEED WITH CONDITIONS\n"
                f"• ARR: $12.5M | NRR: 128% | Runway: 18 Months\n"
                f"• Key Bull Driver: 4.2x LTV/CAC in Fortune 500 cohort\n"
                f"• Key Bear Risk: Top 5 customers represent 34% of ARR\n"
                f"Full 20-section Investment Memo generated & available in Copilot."
            )
            if opp.opp_id not in self._chatter_feed:
                self._chatter_feed[opp.opp_id] = []
            self._chatter_feed[opp.opp_id].append({
                "post_id": post_id,
                "body": post_body,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            return AgentforceActionResponse(
                success=True,
                action_name=request.action_name,
                output_parameters={
                    "chatter_post_id": post_id,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "opp_id": opp.opp_id
                },
                chatter_post_created=True,
                execution_time_ms=elapsed
            )

        else:
            return AgentforceActionResponse(
                success=False,
                action_name=request.action_name,
                output_parameters={"error": f"Unknown Agentforce action '{request.action_name}'."},
                chatter_post_created=False,
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2)
            )

    def sync_data_cloud_zero_copy(self) -> SalesforceDataCloudSyncResult:
        """
        Simulates Salesforce Data Cloud Zero-Copy Lakehouse federation.
        Reads live metadata directly from Data Cloud DMOs without physical ETL copying.
        """
        start = time.perf_counter()
        zero_copy_dmos = [
            "ssot__Opportunity__dlm",
            "ssot__Account__dlm",
            "ciso__DealRoomDocument__dlm",
            "fin__FinancialStatement__dlm"
        ]
        duration = round((time.perf_counter() - start) * 1000, 2)

        return SalesforceDataCloudSyncResult(
            records_ingested=len(self._opportunities),
            zero_copy_tables=zero_copy_dmos,
            sync_status="FEDERATED_ACTIVE",
            duration_ms=duration
        )


salesforce_service = SalesforceService()
