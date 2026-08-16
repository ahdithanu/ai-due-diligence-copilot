import re
import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    ContradictionRecord,
    MaterialityLevel,
    ClaimNode,
    EvidenceRecord
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)


class CrossExaminerNode(BaseNode):
    """
    Cross Examiner Node: Scans across specialist analyses, financial metrics, and evidence records
    to identify contradictions (e.g., revenue discrepancy between pitch deck and audited statements, customer count mismatch).
    Appends ContradictionRecords to state.contradictions.
    """

    def __init__(
        self,
        name: str = "CrossExaminer",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Identifies contradictions across specialist analyses and evidence", model_adapter=model_adapter)

    async def process(self, state: DiligenceState) -> DiligenceState:
        existing_contradiction_keys = {
            (c.claim_a_id, c.claim_b_id) for c in state.contradictions
        } | {
            (c.claim_b_id, c.claim_a_id) for c in state.contradictions
        }

        new_contradictions: List[ContradictionRecord] = []

        if self.model_adapter:
            prompt = (
                f"Perform cross-examination across all specialist analyses and evidence for company '{state.company_name}'.\n"
                f"Specialist Domains Evaluated: {list(state.specialist_analyses.keys())}\n"
                f"Total Evidence Records: {len(state.evidence_records)}\n"
                f"Identify any conflicting metrics, revenue discrepancies between pitch deck and financials, or customer count mismatches."
            )
            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=List[ContradictionRecord]
            )
            if isinstance(generated, list):
                new_contradictions.extend(generated)
        else:
            # Deterministic cross-examination heuristic
            # 1. Collect all claim nodes from specialist analyses and evidence records
            all_claims: List[Tuple[str, str, str]] = []  # (claim_id, text, source_info)

            for domain, analysis in state.specialist_analyses.items():
                for claim in analysis.claims:
                    all_claims.append((claim.id, claim.text, f"Specialist Analysis ({domain})"))

            for ev in state.evidence_records:
                all_claims.append((ev.id, ev.content, f"Evidence Document ({ev.document_id})"))

            # Extract numbers associated with specific key terms in claims (preferring monetary, percentage, or scaled numbers over 4-digit years)
            num_pattern = re.compile(r"(\$?\d+(?:\.\d+)?\s*(?:M|B|K|million|billion|k|%)?)", re.IGNORECASE)

            def get_metric_numbers(text: str) -> List[str]:
                matches = num_pattern.findall(text)
                cleaned = []
                for m in matches:
                    val = m.strip()
                    # Skip 4-digit year strings like 2023, 2024 unless prefixed with $ or suffixed with M/B/K/%
                    if len(val) == 4 and val.isdigit() and (val.startswith("20") or val.startswith("19")):
                        continue
                    cleaned.append(val.replace("$", "").replace("%", "").strip())
                return cleaned

            # Topics to cross-examine
            topics = [
                ("revenue", ["revenue", "arr", "mrr", "sales"]),
                ("customer_count", ["customer", "client", "logo", "account"]),
                ("margin", ["gross margin", "operating margin", "margin"]),
                ("market_size", ["tam", "sam", "som", "market size"])
            ]

            topic_claims: Dict[str, List[Tuple[str, str, str]]] = {t[0]: [] for t in topics}

            for cid, text, source in all_claims:
                text_lower = text.lower()
                for topic_name, keywords in topics:
                    if any(kw in text_lower for kw in keywords):
                        topic_claims[topic_name].append((cid, text, source))

            # Cross examine within each topic
            for topic_name, claims_list in topic_claims.items():
                if len(claims_list) < 2:
                    continue

                for i in range(len(claims_list)):
                    for j in range(i + 1, len(claims_list)):
                        id_a, text_a, src_a = claims_list[i]
                        id_b, text_b, src_b = claims_list[j]

                        if id_a == id_b:
                            continue

                        # Extract numbers
                        nums_a = get_metric_numbers(text_a)
                        nums_b = get_metric_numbers(text_b)

                        if nums_a and nums_b:
                            # Compare distinct numbers if sources differ (e.g. deck vs statement)
                            val_a = nums_a[0]
                            val_b = nums_b[0]

                            if val_a != val_b:
                                # Check if they differ significantly
                                desc = f"Discrepancy detected in {topic_name}: '{text_a}' ({src_a}) vs '{text_b}' ({src_b})."
                                record = ContradictionRecord(
                                    id=str(uuid.uuid4()),
                                    claim_a_id=id_a,
                                    claim_b_id=id_b,
                                    description=desc,
                                    materiality=MaterialityLevel.HIGH,
                                    status="OPEN"
                                )
                                new_contradictions.append(record)


        # Append deduplicated contradictions
        for record in new_contradictions:
            key = (record.claim_a_id, record.claim_b_id)
            if key not in existing_contradiction_keys:
                state.contradictions.append(record)
                existing_contradiction_keys.add(key)
                existing_contradiction_keys.add((record.claim_b_id, record.claim_a_id))

        if any(c.status != "RESOLVED" and c.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL] for c in state.contradictions):
            state.human_review_required = True
            reason = f"Cross-examination identified {len(state.contradictions)} unresolved evidence contradiction(s)."
            if reason not in state.human_review_reasons:
                state.human_review_reasons.append(reason)

        state.status = DiligenceStatus.CROSS_EXAMINATION
        return state
