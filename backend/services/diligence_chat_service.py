import uuid
from typing import List, Dict, Any, Tuple
from backend.domain.schemas import DiligenceState, ChatMessage, DataRoomRequest, EvidenceRecord

class DiligenceChatService:
    def process_query(self, state: DiligenceState, question: str) -> Tuple[ChatMessage, List[DataRoomRequest]]:
        """
        Processes user Q&A query against DiligenceState evidence records and financial metrics.
        Returns a ChatMessage (with grounded citations) and auto-generated DataRoomRequests.
        """
        question_lower = question.lower()
        matched_citations = []
        matching_evidence_text = []

        # 1. Search evidence records for relevant matches
        if state.evidence_records:
            keywords = [k for k in ["arr", "revenue", "growth", "margin", "nrr", "churn", "customer", "valuation", "risk", "team", "legal", "cac", "runway", "moat", "debt"] if k in question_lower]
            for ev in state.evidence_records:
                content_lower = ev.content.lower()
                sec_lower = (ev.section_title or "").lower()
                
                if any(kw in content_lower or kw in sec_lower for kw in keywords) or not keywords:
                    matched_citations.append(ev.id)
                    loc_str = f"Page {ev.page_number}" if ev.page_number else (ev.section_title or "Doc Evidence")
                    matching_evidence_text.append(f"[{loc_str}] {ev.content}")

        matched_citations = matched_citations[:5]

        # 2. Build answer text grounded in state and evidence
        context_intro = f"Regarding '{question}' for **{state.company_name}** ({state.target_round}, {state.industry}):"
        
        if matching_evidence_text:
            evidence_summary = "\n".join(matching_evidence_text[:3])
            answer_content = (
                f"{context_intro}\n\n"
                f"**Extracted Evidence Findings:**\n{evidence_summary}\n\n"
                f"Based on extracted evidence, {state.company_name} shows strong indicators in its core market segment. "
                f"However, additional formal documentation is recommended for complete institutional verification."
            )
        else:
            metrics_summary = []
            if state.financial_metrics:
                for fm in state.financial_metrics[:4]:
                    metrics_summary.append(f"- **{fm.metric_name}**: {fm.value} {fm.unit} ({fm.period})")
            
            metrics_str = "\n".join(metrics_summary) if metrics_summary else "No financial metrics extracted yet."
            
            answer_content = (
                f"{context_intro}\n\n"
                f"**Current Workspace Financial Snapshot:**\n{metrics_str}\n\n"
                f"Investment Status: {state.status.value if hasattr(state.status, 'value') else state.status}. "
                f"Recommendation: {state.recommendation or 'Under Review'} (Confidence: {state.confidence_score or 'N/A'})."
            )

        # 3. Auto-generate Data Room Document Requests based on query intent & missing evidence
        new_requests: List[DataRoomRequest] = []
        existing_doc_types = {r.document_needed.lower() for r in state.data_room_requests}

        def add_request(category: str, doc_needed: str, priority: str, rationale: str):
            if doc_needed.lower() not in existing_doc_types:
                req = DataRoomRequest(
                    category=category,
                    document_needed=doc_needed,
                    priority=priority,
                    status="PENDING",
                    rationale=rationale
                )
                new_requests.append(req)
                existing_doc_types.add(doc_needed.lower())

        if any(w in question_lower for w in ["audited", "financial", "revenue", "arr", "margin", "tax", "p&l", "accounting"]):
            add_request(
                category="Financial",
                doc_needed="2-Year Audited Financial Statements & Monthly P&L",
                priority="HIGH",
                rationale="Required to independently verify historical revenue growth, gross margins, and operating burn rate."
            )
            add_request(
                category="Financial",
                doc_needed="Quality of Earnings (QofE) Report",
                priority="HIGH",
                rationale="Confirm non-recurring revenue items and quality of reported ARR."
            )

        if any(w in question_lower for w in ["churn", "customer", "retention", "nrr", "concentration", "cohort"]):
            add_request(
                category="Commercial",
                doc_needed="Customer Cohort Retention & Concentration Matrix",
                priority="HIGH",
                rationale="Analyze net revenue retention, logo expansion, and top customer revenue concentration risk."
            )

        if any(w in question_lower for w in ["cap table", "valuation", "waterfall", "shares", "investor", "liquidation"]):
            add_request(
                category="Legal & Governance",
                doc_needed="Fully Diluted Cap Table & Shareholder Rights Agreement",
                priority="HIGH",
                rationale="Validate liquidation preference multipliers, anti-dilution provisions, and option pool sizing."
            )

        if any(w in question_lower for w in ["tech", "product", "architecture", "security", "soc2", "ip", "patent"]):
            add_request(
                category="Technology & IP",
                doc_needed="SOC 2 Type II Audit & IP Assignment Agreements",
                priority="MEDIUM",
                rationale="Verify enterprise security compliance and proprietary technology ownership."
            )

        if not new_requests and len(state.data_room_requests) == 0:
            add_request(
                category="General Diligence",
                doc_needed="Management Presentation & Detailed Financial Model",
                priority="MEDIUM",
                rationale="Standard institutional data room requirement for diligence completion."
            )

        # 4. Construct ChatMessage
        assistant_message = ChatMessage(
            role="assistant",
            content=answer_content,
            evidence_citations=matched_citations
        )

        return assistant_message, new_requests

def process_diligence_chat(state: DiligenceState, question: str) -> Tuple[ChatMessage, List[DataRoomRequest]]:
    service = DiligenceChatService()
    return service.process_query(state, question)
