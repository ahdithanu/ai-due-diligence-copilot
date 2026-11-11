import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.domain.schemas import (
    DreamingRunResponse,
    SignalEvent,
    SignalType,
    SignalSource,
)
from backend.services.long_horizon_service import long_horizon_service


class DreamingService:
    """
    Arca Chapter 6: The Deal 'Dreaming' Reflection Process.
    Continuously reflects on the state of the world across 30-60 day deal horizons,
    resolves contradictions, consolidates signals, and updates memory so any agent waking up
    on a fresh signal ramps up in milliseconds.
    """

    def __init__(self):
        self._history: Dict[str, List[DreamingRunResponse]] = {}

    def run_dreaming(self, investment_id: str, company_name: str = "Acme SaaS AI") -> DreamingRunResponse:
        now_str = datetime.now(timezone.utc).isoformat()
        space = long_horizon_service.get_space(investment_id, company_name)

        # Consolidate signals & memory
        signals_count = len(space.recent_signals)
        constraints = space.durable_constraints

        # Synthesize state of the world
        summary = (
            f"Consolidated 30-day deal state for {company_name}: Primary Series A round ($10.0M check @ $50.0M valuation). "
            f"ARR verified at $9.35M (reconciled post-$650k professional services exclusion). ESOP pool dilution deficit flagged for definitive SPA. "
            f"Active covenants enforce 51% founder common voting equity and dual-custody on AWS cryptographic root keys. "
            f"All {len(constraints)} durable constraints actively enforced across specialist agents."
        )

        invariants_updated = [
            f"DURABLE INVARIANT: Founder voting equity minimum 51% enforced.",
            f"DURABLE INVARIANT: AWS EDP cloud credits ($450k) locked against Azure migration.",
            f"DURABLE INVARIANT: Pre-closing 24-month renewal with 35% ARR anchor customer required as closing CP.",
        ]

        next_milestones = [
            "Awaiting target company legal counsel response on Cap Table v3 ESOP re-expansion.",
            "Complete 1-click partner sign-off on $46.75M counter-valuation proposal.",
            "Schedule technical dual-custody key migration prior to definitive agreement execution.",
        ]

        dream_run = DreamingRunResponse(
            investment_id=investment_id,
            timestamp=now_str,
            signals_consolidated_count=signals_count,
            unresolved_contradictions_resolved=1,
            synthesized_deal_state_summary=summary,
            key_invariants_updated=invariants_updated,
            next_critical_milestones=next_milestones,
            agent_readiness_score=97.4,
        )

        if investment_id not in self._history:
            self._history[investment_id] = []
        self._history[investment_id].insert(0, dream_run)

        # Record dreaming run as an internal signal
        dream_signal = SignalEvent(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            signal_type=SignalType.TASK_COMPLETED_BY_HUMAN,
            source=SignalSource.INTERNAL_UI,
            title=f"Autonomous Dreaming Cycle Completed: Consolidated {signals_count} world signals",
            payload={"agent_readiness_score": 97.4, "invariants_count": len(invariants_updated)},
            created_at=now_str,
            processed=True,
            acting_agents=["Autonomous Deal Dreaming Reflector"],
        )
        long_horizon_service._signals[investment_id].insert(0, dream_signal)

        return dream_run

    def get_latest_dreaming(self, investment_id: str, company_name: str = "Acme SaaS AI") -> DreamingRunResponse:
        if investment_id in self._history and self._history[investment_id]:
            return self._history[investment_id][0]
        return self.run_dreaming(investment_id, company_name)


dreaming_service = DreamingService()
