import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from backend.domain.schemas import StaffEditFeedbackRecord, StaffEditRequest

EVAL_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "eval", "staff_eval_store.jsonl")


class StaffFeedbackEvalService:
    """
    Arca Chapter 15: Every staff edit or cancellation comes with a 'Why' and becomes an eval.
    Pipes human corrections coupled with agent traces into a first-class eval dataset.
    """

    def __init__(self):
        self._records: Dict[str, List[StaffEditFeedbackRecord]] = {}
        self._ensure_store_dir()

    def _ensure_store_dir(self):
        store_dir = os.path.dirname(EVAL_STORE_PATH)
        if not os.path.exists(store_dir):
            os.makedirs(store_dir, exist_ok=True)

    def record_staff_edit(
        self, investment_id: str, req: StaffEditRequest
    ) -> StaffEditFeedbackRecord:
        now_str = datetime.now(timezone.utc).isoformat()
        trace_id = f"trace-{str(uuid.uuid4())[:8]}"
        eval_id = f"eval-cand-{str(uuid.uuid4())[:8]}"

        record = StaffEditFeedbackRecord(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            timestamp=now_str,
            target_field=req.target_field,
            agent_original_value=req.agent_original_value,
            human_adjusted_value=req.human_adjusted_value,
            reason_why=req.reason_why,
            editor_role=req.editor_role,
            agent_trace_id=trace_id,
            eval_candidate_id=eval_id,
        )

        if investment_id not in self._records:
            self._records[investment_id] = []
        self._records[investment_id].insert(0, record)

        # Append to persistent JSONL eval dataset
        try:
            with open(EVAL_STORE_PATH, "a", encoding="utf-8") as f:
                payload = {
                    "eval_id": eval_id,
                    "investment_id": investment_id,
                    "target_field": req.target_field,
                    "agent_original": req.agent_original_value,
                    "human_adjusted": req.human_adjusted_value,
                    "reason_why": req.reason_why,
                    "editor_role": req.editor_role,
                    "trace_id": trace_id,
                    "timestamp": now_str,
                }
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            # Non-blocking logging failure
            pass

        return record

    def get_staff_edits(self, investment_id: str) -> List[StaffEditFeedbackRecord]:
        if investment_id not in self._records:
            # Seed with institutional demo edits if empty
            now_str = datetime.now(timezone.utc).isoformat()
            self._records[investment_id] = [
                StaffEditFeedbackRecord(
                    id=str(uuid.uuid4()),
                    investment_id=investment_id,
                    timestamp=now_str,
                    target_field="proposed_entry_valuation_usd",
                    agent_original_value=50_000_000.0,
                    human_adjusted_value=46_750_000.0,
                    reason_why="QoE audit identified $650k non-recurring professional services fee; normalized 12.0x ARR entry multiple dictates $46.75M entry.",
                    editor_role="Deal Lead",
                    agent_trace_id="trace-qoe-001",
                    eval_candidate_id="eval-cand-001",
                ),
                StaffEditFeedbackRecord(
                    id=str(uuid.uuid4()),
                    investment_id=investment_id,
                    timestamp=now_str,
                    target_field="series_a_liquidation_preference",
                    agent_original_value="1.0x Participating with 3x Cap",
                    human_adjusted_value="1.0x Non-Participating Preferred",
                    reason_why="Founder Elena stated during partner call that participating preferred is an absolute dealbreaker for syndicate alignment.",
                    editor_role="IC Partner",
                    agent_trace_id="trace-term-002",
                    eval_candidate_id="eval-cand-002",
                ),
            ]
        return self._records[investment_id]


staff_feedback_eval_service = StaffFeedbackEvalService()
